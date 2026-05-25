import csv
import json
import requests
import time
import os
from collections import defaultdict

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

GITHUB_TOKEN=os.getenv('GITHUB_TOKEN')
POSITIVE_WORDS_EN = {
    'great', 'excellent', 'awesome', 'amazing', 'perfect', 'best', 'good',
    'love', 'like', 'fantastic', 'wonderful', 'brilliant', 'superb',
    'helpful', 'useful', 'nice', 'cool', 'interesting', 'impressive',
    'thank', 'thanks', 'appreciate', 'congratulations', 'well done'
}

NEGATIVE_WORDS_EN = {
    'bad', 'terrible', 'awful', 'horrible', 'worse', 'worst',
    'problem', 'issue', 'bug', 'error', 'broken', 'failed', 'fatal',
    'hate', 'dislike', 'annoying', 'frustrating', 'difficult', 'slow',
    'crash', 'error', 'fail', 'broken', 'buggy', 'vulnerable'
}

def analyze_sentiment(text):
    if not text or text.strip() == '':
        return 'neutral', 0.0

    text = str(text).strip()

    if TEXTBLOB_AVAILABLE:
        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity

            if sentiment_score > 0.1:
                return 'positive', sentiment_score
            elif sentiment_score < -0.1:
                return 'negative', sentiment_score
            else:
                return 'neutral', sentiment_score
        except Exception:
            pass

    text_lower = text.lower()
    positive_count = sum(1 for word in POSITIVE_WORDS_EN if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS_EN if word in text_lower)

    if positive_count > negative_count:
        score = positive_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0
        return 'positive', score
    elif negative_count > positive_count:
        score = -negative_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0
        return 'negative', score
    else:
        return 'neutral', 0.0

# 修复点1：添加请求头，避免API限流/403
def get_github_issues(owner, repo, max_pages=3):
    issues = []
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    # 添加GitHub API请求头（必填，否则可能被限流）
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'User-Agent': 'GitHub-Sentiment-Analyzer/1.0',  # 自定义User-Agent
        'Accept': 'application/vnd.github.v3+json'
    }

    if not GITHUB_TOKEN:
        print("❌ 错误：未配置 GitHub Token！")
        return []

    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                f"{url}?page={page}&per_page=30",
                headers=headers,  # 加入请求头
                timeout=15
            )
            # 处理API限流
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 60)
                print(f"⚠️ API限流，等待{sleep_time:.0f}秒后重试...")
                time.sleep(sleep_time)
                continue
            if response.status_code != 200:
                print(f"❌ 获取Issues失败，状态码: {response.status_code}")
                break

            page_issues = response.json()
            if not page_issues:
                break

            for issue in page_issues:
                # 过滤Pull Request（只保留纯Issue）
                if 'pull_request' not in issue:
                    issues.append({
                        'number': issue.get('number'),  # 修复点2：保留Issue编号（关键）
                        'title': issue.get('title', ''),
                        'body': issue.get('body', ''),
                        'user': issue.get('user', {}).get('login', ''),
                        'user_url': issue.get('user', {}).get('html_url', ''),
                        'state': issue.get('state', ''),
                        'created_at': issue.get('created_at', ''),
                        'comments': issue.get('comments', 0)
                    })
            time.sleep(1)
        except Exception as e:
            print(f"获取issues失败: {e}")
            break

    return issues

# 修复点3：请求头+错误处理
def get_issue_comments(owner, repo, issue_number):
    comments = []
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'User-Agent': 'GitHub-Sentiment-Analyzer/1.0',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        # 处理API限流
        if response.status_code == 403:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - time.time(), 60)
            print(f"⚠️ API限流，等待{sleep_time:.0f}秒后重试...")
            time.sleep(sleep_time)
            response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            for comment in response.json():
                comments.append({
                    'body': comment.get('body', ''),
                    'user': comment.get('user', {}).get('login', ''),
                    'user_url': comment.get('user', {}).get('html_url', ''),
                    'created_at': comment.get('created_at', '')
                })
        else:
            print(f"❌ 获取Issue #{issue_number} 评论失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"获取评论失败: {e}")

    return comments

# 修复点4：请求头+错误处理
def get_user_info(username):
    url = f"https://api.github.com/users/{username}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'User-Agent': 'GitHub-Sentiment-Analyzer/1.0',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 403:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - time.time(), 60)
            print(f"⚠️ API限流，等待{sleep_time:.0f}秒后重试...")
            time.sleep(sleep_time)
            response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            user_data = response.json()
            return {
                'login': user_data.get('login', ''),
                'name': user_data.get('name', ''),
                'company': user_data.get('company', ''),
                'location': user_data.get('location', ''),
                'followers': user_data.get('followers', 0),
                'following': user_data.get('following', 0),
                'public_repos': user_data.get('public_repos', 0),
                'created_at': user_data.get('created_at', '')
            }
        else:
            print(f"❌ 获取用户 {username} 失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"获取用户信息失败 {username}: {e}")

    return None

def analyze_repository(owner, repo_name, max_issues=10):
    print(f"正在分析仓库: {owner}/{repo_name}")

    issues = get_github_issues(owner, repo_name)[:max_issues]

    # 修复点5：更严谨的“无Issues”判断
    if not issues:
        print(f"⚠️ 未获取到任何公开Issue")
        return None

    all_comments = []
    user_info_cache = {}

    for issue in issues:
        # 修复点6：使用真实的Issue编号（而非列表索引）
        issue_number = issue.get('number')
        if not issue_number:
            continue
        issue_comments = get_issue_comments(owner, repo_name, issue_number)
        all_comments.extend(issue_comments)

        user_login = issue.get('user')
        if user_login and user_login not in user_info_cache:
            user_info_cache[user_login] = get_user_info(user_login)
            time.sleep(0.5)

    issue_sentiments = []

    for issue in issues:
        text = f"{issue.get('title', '')} {issue.get('body', '')}"
        sentiment, score = analyze_sentiment(text)
        issue_sentiments.append({
            'title': issue.get('title'),
            'sentiment': sentiment,
            'score': score,
            'user': issue.get('user')
        })

    comment_sentiments = []
    for comment in all_comments:
        sentiment, score = analyze_sentiment(comment.get('body', ''))
        comment_sentiments.append({
            'body': comment.get('body')[:100] + '...' if len(comment.get('body', '')) > 100 else comment.get('body'),
            'sentiment': sentiment,
            'score': score,
            'user': comment.get('user')
        })

        user_login = comment.get('user')
        if user_login and user_login not in user_info_cache:
            user_info_cache[user_login] = get_user_info(user_login)
            time.sleep(0.5)

    return {
        'repo': f"{owner}/{repo_name}",
        'issues_count': len(issues),
        'comments_count': len(all_comments),
        'issue_sentiments': issue_sentiments,
        'comment_sentiments': comment_sentiments,
        'users': user_info_cache
    }

def analyze_trending_csv(csv_file, target_count=3):
    results = []
    skipped = []
    analyzed_count = 0

    print(f"\n正在从 {csv_file} 寻找 {target_count} 个有公开issues的项目...")

    with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if analyzed_count >= target_count:
                break

            url = row.get('url', '')
            repo_name_csv = row.get('name', '')

            if not url:
                print(f"  ⏭️ 跳过 #{i+1}: {repo_name_csv} (无URL)")
                skipped.append({
                    'repo': repo_name_csv,
                    'reason': '无GitHub链接'
                })
                continue

            parts = url.replace('https://github.com/', '').split('/')
            # 修复点7：处理URL中多余的路径（比如 /owner/repo/xxx）
            if len(parts) < 2:
                print(f"  ⏭️ 跳过 #{i+1}: {repo_name_csv} (URL格式不正确)")
                skipped.append({
                    'repo': repo_name_csv,
                    'reason': 'URL格式不正确'
                })
                continue
            owner = parts[0]
            repo_name = parts[1].split('#')[0].split('?')[0]  # 去除锚点/参数

            try:
                print(f"  🔍 尝试 #{i+1}: {owner}/{repo_name}...")
                repo_analysis = analyze_repository(owner, repo_name)

                if repo_analysis is None:
                    print(f"  ⏭️ 跳过 #{i+1}: {owner}/{repo_name} (无公开issues或评论)")
                    skipped.append({
                        'repo': f"{owner}/{repo_name}",
                        'reason': '无公开issues或评论'
                    })
                    time.sleep(1)
                    continue

                results.append(repo_analysis)
                analyzed_count += 1
                print(f"  ✅ 成功 #{analyzed_count}: {owner}/{repo_name} ({repo_analysis['issues_count']} issues, {repo_analysis['comments_count']} 评论)")
                time.sleep(2)

            except Exception as e:
                print(f"  ❌ 分析失败 #{i+1}: {owner}/{repo_name} - {e}")
                skipped.append({
                    'repo': f"{owner}/{repo_name}",
                    'reason': f'分析失败: {str(e)}'
                })
                time.sleep(1)

    if analyzed_count < target_count:
        print(f"\n⚠️ 警告: 仅找到 {analyzed_count}/{target_count} 个有公开issues的项目")

    if skipped:
        print(f"\n跳过的项目 ({len(skipped)}个):")
        for item in skipped:
            print(f"  - {item['repo']}: {item['reason']}")

    return results, skipped

def generate_summary_report(analyses):
    report = {
        'total_repos': len(analyses),
        'repos': [],
        'overall_sentiment': {'positive': 0, 'neutral': 0, 'negative': 0},
        'top_users': []
    }

    for analysis in analyses:
        issue_sentiments = [item['sentiment'] for item in analysis['issue_sentiments']]
        comment_sentiments = [item['sentiment'] for item in analysis['comment_sentiments']]

        repo_sentiment = {
            'positive': issue_sentiments.count('positive') + comment_sentiments.count('positive'),
            'neutral': issue_sentiments.count('neutral') + comment_sentiments.count('neutral'),
            'negative': issue_sentiments.count('negative') + comment_sentiments.count('negative')
        }

        report['overall_sentiment']['positive'] += repo_sentiment['positive']
        report['overall_sentiment']['neutral'] += repo_sentiment['neutral']
        report['overall_sentiment']['negative'] += repo_sentiment['negative']

        report['repos'].append({
            'name': analysis['repo'],
            'issues': len(analysis['issue_sentiments']),
            'comments': len(analysis['comment_sentiments']),
            'sentiment': repo_sentiment
        })

    sorted_users = []
    for analysis in analyses:
        for user_login, user_data in analysis.get('users', {}).items():
            if user_data and user_data.get('followers', 0) > 0:
                sorted_users.append((user_login, user_data))

    sorted_users.sort(key=lambda x: x[1].get('followers', 0), reverse=True)
    report['top_users'] = [
        {'login': user, 'followers': data.get('followers', 0)}
        for user, data in sorted_users[:10]
    ]

    return report

def main():
    print("=" * 70)
    print("GitHub 仓库评论情感分析 (智能跳过无issues项目)")
    print("=" * 70)
    print(f"情感分析引擎: {'textblob' if TEXTBLOB_AVAILABLE else '基于词典'}")
    print()

    csv_files = ['../data/github_trending_daily.csv', '../data/github_trending_weekly.csv', '../data/github_trending_monthly.csv']
    target_count = 3

    all_reports = {}

    for csv_file in csv_files:
        print(f"\n{'='*70}")
        print(f"📊 分析 {csv_file}")
        print('='*70)

        analyses, skipped = analyze_trending_csv(csv_file, target_count=target_count)

        if analyses:
            report = generate_summary_report(analyses)
            all_reports[csv_file] = {
                'analyses': analyses,
                'summary': report,
                'skipped': skipped
            }

            output_file = f'../data/{csv_file.split("/")[-1]}_comments_analysis.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, ensure_ascii=False, indent=2)

            print(f"\n📄 报告已保存: {output_file}")

            total = sum(report['overall_sentiment'].values())
            if total > 0:
                print(f"\n📈 整体情感分布:")
                print(f"   正面: {report['overall_sentiment']['positive']} ({report['overall_sentiment']['positive']/total*100:.1f}%)")
                print(f"   中性: {report['overall_sentiment']['neutral']} ({report['overall_sentiment']['neutral']/total*100:.1f}%)")
                print(f"   负面: {report['overall_sentiment']['negative']} ({report['overall_sentiment']['negative']/total*100:.1f}%)")

            print(f"\n📦 仓库详情:")
            for repo in report['repos']:
                total_repo = sum(repo['sentiment'].values())
                print(f"\n   {repo['name']}")
                print(f"   Issues: {repo['issues']}, Comments: {repo['comments']}")
                if total_repo > 0:
                    print(f"   情感 - 正面: {repo['sentiment']['positive']} ({repo['sentiment']['positive']/total_repo*100:.1f}%), "
                          f"中性: {repo['sentiment']['neutral']} ({repo['sentiment']['neutral']/total_repo*100:.1f}%), "
                          f"负面: {repo['sentiment']['negative']} ({repo['sentiment']['negative']/total_repo*100:.1f}%)")

            if report['top_users']:
                print(f"\n👥 活跃用户 (Top 5 by followers):")
                for user in report['top_users'][:5]:
                    print(f"   @{user['login']} - {user['followers']} followers")
        else:
            print(f"\n❌ 未能找到任何有公开issues的项目")
            all_reports[csv_file] = {
                'analyses': [],
                'summary': None,
                'skipped': skipped
            }

    print(f"\n{'='*70}")
    print("🎉 分析完成!")
    print('='*70)

if __name__ == '__main__':
    main()