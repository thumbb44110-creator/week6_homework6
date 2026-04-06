#!/usr/bin/env python3
"""
檢查 Notebook 各 Cell 設定
"""

import json
from pathlib import Path

def check_notebook_cells():
    """檢查 Notebook 各 Cell 設定"""
    notebook_path = Path('Week6_Shootout.ipynb')
    
    if not notebook_path.exists():
        print("Notebook 檔案不存在")
        return
    
    print("=" * 60)
    print("Notebook Cell 設定檢查")
    print("=" * 60)
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        cells = notebook.get('cells', [])
        total_cells = len(cells)
        
        print(f"總 Cell 數量: {total_cells}")
        print("\nCell 詳細檢查:")
        
        issues = []
        
        for i, cell in enumerate(cells, 1):
            cell_type = cell.get('cell_type', 'unknown')
            metadata = cell.get('metadata', {})
            source = cell.get('source', [])
            
            # 檢查 source 格式
            if isinstance(source, list):
                source_text = ''.join(source)
            else:
                source_text = str(source)
            
            # 檢查 Unicode 問題
            try:
                source_text.encode('cp950')
                unicode_ok = True
            except UnicodeEncodeError:
                unicode_ok = False
                issues.append(f"Cell {i}: Unicode 編碼問題")
            
            # 檢查基本內容
            has_content = len(source_text.strip()) > 0 if source_text else False
            
            print(f"\nCell {i}:")
            print(f"  類型: {cell_type}")
            print(f"  內容長度: {len(source_text)} 字符")
            print(f"  有內容: {'是' if has_content else '否'}")
            print(f"  Unicode 正常: {'是' if unicode_ok else '否'}")
            
            # 檢查關鍵功能
            if cell_type == 'code':
                if 'print_cell_header' in source_text:
                    print(f"  功能: 包含 print_cell_header")
                if 'load_rainfall_data' in source_text:
                    print(f"  功能: 包含資料載入")
                if 'time_strategy' in source_text:
                    print(f"  功能: 包含智慧時間策略")
                if '智慧資料處理' in source_text:
                    print(f"  功能: 智慧資料處理版本")
        
        print(f"\n問題總結:")
        if issues:
            for issue in issues:
                print(f"  ❌ {issue}")
        else:
            print("  ✅ 未發現明顯問題")
        
        # 檢查關鍵 Cells
        print(f"\n關鍵 Cells 狀態:")
        key_cells = {
            1: "環境設定",
            2: "資料處理函數", 
            3: "凱米颱風載入",
            4: "鳳凰颱風載入",
            6: "凱米 Variogram",
            8: "鳳凰 Variogram",
            14: "成果總結"
        }
        
        for cell_num, description in key_cells.items():
            if cell_num <= total_cells:
                cell = cells[cell_num - 1]
                source = cell.get('source', [])
                if isinstance(source, list):
                    source_text = ''.join(source)
                else:
                    source_text = str(source)
                
                has_content = len(source_text.strip()) > 0
                print(f"  Cell {cell_num} ({description}): {'OK' if has_content else 'FAIL'}")
            else:
                print(f"  Cell {cell_num} ({description}): FAIL - 不存在")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"檢查失敗: {e}")
        return False

def main():
    """主函數"""
    success = check_notebook_cells()
    
    print("\n" + "=" * 60)
    if success:
        print("Notebook Cell 設定檢查完成")
    else:
        print("發現問題，需要修正")
    print("=" * 60)

if __name__ == "__main__":
    main()
