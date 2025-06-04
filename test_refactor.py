#!/usr/bin/env python3

from modules.code_analysis.auto_refactor import get_auto_refactor
import json

def main():
    print("🔍 Running AXIS Auto-Refactor Analysis...")
    print("=" * 50)
    
    refactor = get_auto_refactor()
    report = refactor.run_refactoring_scan('.')
    
    print(f"📊 REFACTORING SUMMARY")
    print(f"Total Python files analyzed: {report['total_files_analyzed']}")
    print(f"Files needing refactoring: {report['files_needing_refactoring']}")
    print(f"Total lines in large files: {report['total_lines_analyzed']:,}")
    print()
    
    summary = report['summary']
    print(f"🚨 High priority files: {summary['high_priority_files']}")
    print(f"⚠️  Medium priority files: {summary['medium_priority_files']}")
    print(f"📝 Low priority files: {summary['low_priority_files']}")
    print(f"📈 Average lines per large file: {summary['avg_lines_per_large_file']:.1f}")
    print()
    
    print("🎯 TOP 10 FILES NEEDING REFACTORING:")
    print("-" * 50)
    
    for i, file_info in enumerate(report['files'][:10], 1):
        priority_emoji = {"high": "🚨", "medium": "⚠️", "low": "📝"}
        emoji = priority_emoji.get(file_info['priority'], "📄")
        
        print(f"{i:2d}. {emoji} {file_info['path']}")
        print(f"     Lines: {file_info['lines']}, Priority: {file_info['priority']}")
        
        # Show suggestions
        suggestions = file_info.get('suggestions', [])
        if suggestions:
            print(f"     Suggestions: {len(suggestions)} refactoring options")
            for suggestion in suggestions[:2]:  # Show first 2 suggestions
                if suggestion['type'] == 'generic_split':
                    print(f"       → Manual refactoring needed")
                else:
                    print(f"       → {suggestion['content']}")
        print()
    
    print("✅ Analysis complete! Use the suggestions above to refactor large files.")
    
    # Save detailed report
    with open('refactoring_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print("📄 Detailed report saved to: refactoring_report.json")

if __name__ == "__main__":
    main() 