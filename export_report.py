from pymongo import MongoClient
import os

client = MongoClient('mongodb://localhost:27017')
db = client['tech_hotspot']

insights = list(db['insights'].find().sort('created_at', -1).limit(1))

if insights:
    insight = insights[0]

    report = "=" * 70 + "\n"
    report += "                    DeepSeek AI 分析报告\n"
    report += "=" * 70 + "\n\n"

    report += "[基本信息]\n"
    report += "-" * 30 + "\n"
    report += f"分析时间: {insight.get('metadata', {}).get('analyzed_at', 'N/A')}\n"
    report += f"分析集合: {insight.get('metadata', {}).get('collection', 'N/A')}\n"
    report += f"分析项目数: {insight.get('metadata', {}).get('projects_count', 0)}\n"
    report += f"模型: {insight.get('metadata', {}).get('model', 'N/A')}\n\n"

    report += "[趋势识别]\n"
    report += "-" * 30 + "\n"
    for i, trend in enumerate(insight.get('趋势识别', []), 1):
        report += f"{i}. {trend}\n\n"

    report += "[值得关注的项目]\n"
    report += "-" * 30 + "\n"
    for i, project in enumerate(insight.get('值得关注的项目', []), 1):
        report += f"{i}. {project}\n\n"

    report += "[学习路径]\n"
    report += "-" * 30 + "\n"
    for i, path in enumerate(insight.get('学习路径', []), 1):
        report += f"{i}. {path}\n\n"

    report += "[信号挖掘]\n"
    report += "-" * 30 + "\n"
    for i, signal in enumerate(insight.get('信号挖掘', []), 1):
        report += f"{i}. {signal}\n\n"

    report += "=" * 70 + "\n"
    report += "                    报告结束\n"
    report += "=" * 70

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI分析", "output")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = insight.get('metadata', {}).get('analyzed_at', 'unknown').split('T')[0]
    filename = os.path.join(output_dir, f"ai_analysis_report_{timestamp}.txt")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"AI分析报告已导出到: {filename}")
    print()
    print(report)
else:
    print("暂无分析结果，请先运行 AI 分析")

client.close()
