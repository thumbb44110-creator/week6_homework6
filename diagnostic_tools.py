#!/usr/bin/env python3
"""
IDW 插值問題診斷工具
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def diagnose_coordinate_system():
    """診斷坐標系統問題"""
    print("=" * 60)
    print("🔍 坐標系統診斷工具")
    print("=" * 60)
    
    try:
        # 模擬載入資料 (從實際執行環境獲取)
        if 'kaimi_validated' in locals():
            print("📊 檢查凱米颱風坐標範圍...")
            
            # 檢查坐標範圍
            x_min = kaimi_validated['easting'].min()
            x_max = kaimi_validated['easting'].max()
            y_min = kaimi_validated['northing'].min()
            y_max = kaimi_validated['northing'].max()
            
            print(f"  測站 X 範圍: {x_min:.0f} - {x_max:.0f} m")
            print(f"  測站 Y 範圍: {y_min:.0f} - {y_max:.0f} m")
            
            # 檢查是否有異常值
            print(f"  測站數量: {len(kaimi_validated)}")
            print(f"  有效座標數: {kaimi_validated[['easting', 'northing']].notnull().sum().sum()}")
            
            # 檢查雨量值
            rain_min = kaimi_validated['Past24hr'].min()
            rain_max = kaimi_validated['Past24hr'].max()
            print(f"  雨量範圍: {rain_min:.1f} - {rain_max:.1f} mm")
            
        if 'phoenix_validated' in locals():
            print("\n📊 檢查鳳凰颱風坐標範圍...")
            
            x_min = phoenix_validated['easting'].min()
            x_max = phoenix_validated['easting'].max()
            y_min = phoenix_validated['northing'].min()
            y_max = phoenix_validated['northing'].max()
            
            print(f"  測站 X 範圍: {x_min:.0f} - {x_max:.0f} m")
            print(f"  測站 Y 範圍: {y_min:.0f} - {y_max:.0f} m")
            print(f"  測站數量: {len(phoenix_validated)}")
            print(f"  有效座標數: {phoenix_validated[['easting', 'northing']].notnull().sum().sum()}")
            
        if 'grid_info' in locals():
            print("\n📐 檢查插值網格範圍...")
            print(f"  網格 X 範圍: {grid_info['grid_x'].min():.0f} - {grid_info['grid_x'].max():.0f} m")
            print(f"  網格 Y 範圍: {grid_info['grid_y'].min():.0f} - {grid_info['grid_y'].max():.0f} m")
            print(f"  網格尺寸: {grid_info['grid_xx'].shape}")
            
            # 檢查覆蓋情況
            if 'kaimi_validated' in locals():
                kaimi_in_grid = (
                    (kaimi_validated['easting'] >= grid_info['grid_x'].min()) &
                    (kaimi_validated['easting'] <= grid_info['grid_x'].max()) &
                    (kaimi_validated['northing'] >= grid_info['grid_y'].min()) &
                    (kaimi_validated['northing'] <= grid_info['grid_y'].max())
                ).sum()
                print(f"  凱米颱風測站在網格內: {kaimi_in_grid}/{len(kaimi_validated)}")
                
            if 'phoenix_validated' in locals():
                phoenix_in_grid = (
                    (phoenix_validated['easting'] >= grid_info['grid_x'].min()) &
                    (phoenix_validated['easting'] <= grid_info['grid_x'].max()) &
                    (phoenix_validated['northing'] >= grid_info['grid_y'].min()) &
                    (phoenix_validated['northing'] <= grid_info['grid_y'].max())
                ).sum()
                print(f"  鳳凰颱風測站在網格內: {phoenix_in_grid}/{len(phoenix_validated)}")
        
        print("\n💡 診斷建議:")
        print("  1. 如果測站不在網格內，需要調整網格範圍")
        print("  2. 如果坐標有異常值，需要坐標轉換檢查")
        print("  3. 確保 EPSG:3826 坐標系統一致性")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")

def plot_station_distribution():
    """繪製測站分佈圖"""
    print("\n📈 繪製測站分佈圖...")
    
    try:
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # 凱米颱風
        if 'kaimi_validated' in locals():
            ax = axes[0]
            ax.scatter(kaimi_validated['easting'], kaimi_validated['northing'], 
                      c=kaimi_validated['Past24hr'], cmap='Blues', s=50, alpha=0.7)
            ax.set_xlabel('Easting (m)')
            ax.set_ylabel('Northing (m)')
            ax.set_title('凱米颱風測站分佈')
            plt.colorbar(ax.scatter(kaimi_validated['easting'], kaimi_validated['northing'], 
                              c=kaimi_validated['Past24hr'], cmap='Blues', s=50, alpha=0.7), 
                     ax=ax, label='雨量 (mm)')
        
        # 鳳凰颱風
        if 'phoenix_validated' in locals():
            ax = axes[1]
            ax.scatter(phoenix_validated['easting'], phoenix_validated['northing'], 
                      c=phoenix_validated['Past24hr'], cmap='Reds', s=50, alpha=0.7)
            ax.set_xlabel('Easting (m)')
            ax.set_ylabel('Northing (m)')
            ax.set_title('鳳凰颱風測站分佈')
            plt.colorbar(ax.scatter(phoenix_validated['easting'], phoenix_validated['northing'], 
                              c=phoenix_validated['Past24hr'], cmap='Reds', s=50, alpha=0.7), 
                     ax=ax, label='雨量 (mm)')
        
        # 繪製網格範圍
        if 'grid_info' in locals():
            for ax in axes:
                ax.plot([grid_info['grid_x'].min(), grid_info['grid_x'].max()], 
                        [grid_info['grid_y'].min(), grid_info['grid_y'].min()], 'r--', alpha=0.5)
                ax.plot([grid_info['grid_x'].min(), grid_info['grid_x'].max()], 
                        [grid_info['grid_y'].max(), grid_info['grid_y'].max()], 'r--', alpha=0.5)
                ax.plot([grid_info['grid_x'].min(), grid_info['grid_x'].min()], 
                        [grid_info['grid_y'].min(), grid_info['grid_y'].max()], 'r--', alpha=0.5)
                ax.plot([grid_info['grid_x'].max(), grid_info['grid_x'].max()], 
                        [grid_info['grid_y'].min(), grid_info['grid_y'].max()], 'r--', alpha=0.5)
        
        plt.tight_layout()
        
        # 儲存圖片
        output_dir = Path('outputs/diagnostics')
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_dir / 'station_distribution.png', dpi=300, bbox_inches='tight')
        print(f"✅ 測站分佈圖已儲存: outputs/diagnostics/station_distribution.png")
        
        plt.show()
        
    except Exception as e:
        print(f"❌ 繪圖失敗: {e}")

if __name__ == "__main__":
    diagnose_coordinate_system()
    plot_station_distribution()
