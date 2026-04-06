"""
資料處理工具函數
"""

import pandas as pd
import numpy as np
from pyproj import Transformer
from pathlib import Path
from datetime import datetime


def analyze_time_dimension(csv_path):
    """
    分析資料的時間維度特性
    
    Parameters:
    -----------
    csv_path : str or Path
        CSV 檔案路徑
        
    Returns:
    --------
    dict
        時間維度分析結果
    """
    print(f"  分析時間維度: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        
        # 基本時間統計
        time_stats = {
            'total_records': len(df),
            'unique_stations': df['StationId'].nunique(),
            'unique_times': df['DateTime'].nunique(),
            'time_range': {
                'start': df['DateTime'].min(),
                'end': df['DateTime'].max(),
                'duration_hours': pd.to_datetime(df['DateTime'].max()) - pd.to_datetime(df['DateTime'].min())
            },
            'records_per_station': len(df) / df['StationId'].nunique(),
            'time_resolution': None
        }
        
        # 計算時間解析度
        if time_stats['unique_times'] > 1:
            time_diffs = pd.to_datetime(df['DateTime']).drop_duplicates().sort_values().diff().dropna()
            time_stats['time_resolution'] = time_diffs.min().total_seconds() / 60  # 分鐘
        
        print(f"    時間範圍: {time_stats['time_range']['start']} 至 {time_stats['time_range']['end']}")
        print(f"    時間解析度: {time_stats['time_resolution']} 分鐘" if time_stats['time_resolution'] else "    時間解析度: 單一時間點")
        print(f"    測站數量: {time_stats['unique_stations']}")
        print(f"    時間點數: {time_stats['unique_times']}")
        print(f"    總筆數: {time_stats['total_records']}")
        
        return time_stats
        
    except Exception as e:
        print(f"    時間分析失敗: {e}")
        return None


def select_representative_time(df, strategy='peak_rainfall'):
    """
    選擇代表性時間點
    
    Parameters:
    -----------
    df : pd.DataFrame
        原始雨量資料
    strategy : str
        時間選擇策略: 'peak_rainfall', 'max_rainfall_per_station', 'specific_time'
        
    Returns:
    --------
    pd.DataFrame
        篩選後的資料
    """
    print(f"  選擇代表性時間點 (策略: {strategy})...")
    
    try:
        if strategy == 'peak_rainfall':
            # 選擇全區域最大總雨量的時間點
            time_rainfall = df.groupby('DateTime')['Past24hr'].sum().sort_values(ascending=False)
            target_time = time_rainfall.index[0]
            result_df = df[df['DateTime'] == target_time].copy()
            print(f"    選擇全區最大雨量時間: {target_time}")
            
        elif strategy == 'max_rainfall_per_station':
            # 每個測站選擇其最大雨量時間點
            result_df = df.loc[df.groupby('StationId')['Past24hr'].idxmax()].copy()
            print(f"    每測站選擇最大雨量時間點")
            
        elif strategy == 'specific_time':
            # 選擇特定時間點 (颱風巔峰時刻)
            target_time = "2024-07-24 20:00:00"  # 凱米颱風巔峰
            if target_time in df['DateTime'].values:
                result_df = df[df['DateTime'] == target_time].copy()
                print(f"    選擇特定時間: {target_time}")
            else:
                # 如果指定時間不存在，選擇最接近的時間
                available_times = pd.to_datetime(df['DateTime']).unique()
                target_dt = pd.to_datetime(target_time)
                closest_time = available_times[np.abs(available_times - target_dt).argmin()]
                result_df = df[df['DateTime'] == str(closest_time)].copy()
                print(f"    選擇最接近時間: {closest_time}")
        else:
            raise ValueError(f"不支援的策略: {strategy}")
        
        print(f"    篩選結果: {len(df)} → {len(result_df)} 筆")
        return result_df
        
    except Exception as e:
        print(f"    時間選擇失敗: {e}")
        return None


def load_rainfall_data(csv_path, target_counties=['花蓮縣', '宜蘭縣'], time_strategy='peak_rainfall'):
    """
    載入雨量資料並篩選目標縣市 (包含智慧時間處理)
    
    Parameters:
    -----------
    csv_path : str or Path
        CSV 檔案路徑
    target_counties : list
        目標縣市列表
    time_strategy : str
        時間選擇策略: 'peak_rainfall', 'max_rainfall_per_station', 'specific_time', 'all_times'
        
    Returns:
    --------
    pd.DataFrame
        處理後的資料框
    """
    print(f"  載入資料: {csv_path}")
    try:
        # 1. 載入原始資料
        df = pd.read_csv(csv_path)
        print(f"    原始資料: {len(df)} 筆")
        
        # 2. 分析時間維度
        time_stats = analyze_time_dimension(csv_path)
        
        # 3. 篩選目標縣市
        df_filtered = df[df['CountyName'].isin(target_counties)].copy()
        print(f"    篩選目標縣市: {len(df_filtered)} 筆")
        
        # 4. 時間處理策略
        if time_strategy == 'all_times':
            # 保留所有時間點 (原始行為)
            result_df = df_filtered
            print(f"    保留所有時間點: {len(result_df)} 筆")
        else:
            # 應用時間選擇策略
            result_df = select_representative_time(df_filtered, time_strategy)
            
        # 5. 過濾無效值 (-998 和 0)
        if result_df is not None:
            before_count = len(result_df)
            result_df = result_df[result_df['Past24hr'] > 0].copy()
            result_df = result_df[result_df['Past24hr'] != -998].copy()
            after_count = len(result_df)
            
            print(f"    過濾無效值: {before_count} → {after_count} 筆")
            
            # 6. 效能統計
            if time_stats:
                reduction_rate = (1 - len(result_df) / time_stats['total_records']) * 100
                print(f"    效能提升: 資料量減少 {reduction_rate:.1f}%")
        
        return result_df
        
    except Exception as e:
        print(f"    載入失敗: {e}")
        return None


def transform_coordinates(df):
    """
    坐標轉換 WGS84 → EPSG:3826
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含經緯度的資料框
        
    Returns:
    --------
    pd.DataFrame
        加入轉換後坐標的資料框
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)
    
    x_coords, y_coords = transformer.transform(
        df['StationLongitude'].values, 
        df['StationLatitude'].values
    )
    
    df['easting'] = x_coords
    df['northing'] = y_coords
    
    return df


def validate_data(df, event_name):
    """
    驗證資料品質
    
    Parameters:
    -----------
    df : pd.DataFrame
        待驗證的資料
    event_name : str
        事件名稱
        
    Returns:
    --------
    pd.DataFrame
        驗證後的資料
    """
    print(f"\n📊 {event_name} 資料驗證:")
    print(f"  總測站數: {len(df)}")
    print(f"  雨量範圍: {df['Past24hr'].min():.1f} - {df['Past24hr'].max():.1f} mm")
    print(f"  平均雨量: {df['Past24hr'].mean():.1f} mm")
    print(f"  縣市分佈: {df['CountyName'].value_counts().to_dict()}")
    
    return df


def create_interpolation_grid(df, resolution=1000, buffer=5000):
    """
    建立插值網格
    
    Parameters:
    -----------
    df : pd.DataFrame
        測站資料
    resolution : int
        網格解析度 (公尺)
    buffer : int
        緩衝區距離 (公尺)
        
    Returns:
    --------
    tuple
        (grid_x, grid_y, grid_bounds)
    """
    # 計算網格範圍
    min_x, max_x = df['easting'].min() - buffer, df['easting'].max() + buffer
    min_y, max_y = df['northing'].min() - buffer, df['northing'].max() + buffer
    
    # 建立網格
    grid_x = np.arange(min_x, max_x, resolution)
    grid_y = np.arange(min_y, max_y, resolution)
    
    grid_bounds = (min_x, min_y, max_x, max_y)
    
    print(f"📐 網格設定:")
    print(f"  解析度: {resolution}m")
    print(f"  範圍: {min_x:.0f} - {max_x:.0f} (E), {min_y:.0f} - {max_y:.0f} (N)")
    print(f"  網格尺寸: {len(grid_x)} × {len(grid_y)} = {len(grid_x) * len(grid_y)} 點")
    
    return grid_x, grid_y, grid_bounds


def prepare_data_for_interpolation(df):
    """
    準備插值資料
    
    Parameters:
    -----------
    df : pd.DataFrame
        測站資料
        
    Returns:
    --------
    tuple
        (x_coords, y_coords, rainfall_values)
    """
    x_coords = df['easting'].values
    y_coords = df['northing'].values
    rainfall_values = df['Past24hr'].values
    
    return x_coords, y_coords, rainfall_values


if __name__ == "__main__":
    print("🔧 資料處理工具函數載入完成")
