"""
插值方法工具函數
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from pykrige.ok import OrdinaryKriging
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS


def nearest_neighbor_interpolation(grid_x, grid_y, x_coords, y_coords, values):
    """
    最近鄰插值
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
        
    Returns:
    --------
    array
        插值結果網格
    """
    # 建立網格點
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    grid_points = np.column_stack([grid_xx.ravel(), grid_yy.ravel()])
    
    # 最近鄰插值
    tree = cKDTree(np.column_stack([x_coords, y_coords]))
    _, indices = tree.query(grid_points)
    
    result = values[indices].reshape(grid_xx.shape)
    
    return result


def idw_interpolation(grid_x, grid_y, x_coords, y_coords, values, power=2, smoothing=0):
    """
    反距離權重插值 (IDW)
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
    power : float
        距離權重參數
    smoothing : float
        平滑參數
        
    Returns:
    --------
    array
        插值結果網格
    """
    # 建立網格點
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    grid_points = np.column_stack([grid_xx.ravel(), grid_yy.ravel()])
    
    # IDW 插值
    result = griddata(
        (x_coords, y_coords), values, grid_points,
        method='linear' if power == 1 else 'cubic',
        fill_value=0
    )
    
    # 如果使用 cubic 方法，實現 IDW
    if power != 1:
        # 計算距離權重
        distances = np.sqrt((grid_points[:, :, np.newaxis] - np.array([x_coords, y_coords]).T)**2).sum(axis=1)
        
        # 避免除零
        distances = np.maximum(distances, 1e-10)
        
        # 計算權重
        weights = 1.0 / (distances ** power)
        weights_sum = np.sum(weights, axis=1, keepdims=True)
        weights = weights / weights_sum
        
        # 加權平均
        result = np.sum(weights * values, axis=1)
    
    return result.reshape(grid_xx.shape)


def kriging_interpolation(grid_x, grid_y, x_coords, y_coords, values, variogram_model='spherical'):
    """
    Kriging 插值
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
    variogram_model : str
        variogram 模型類型
        
    Returns:
    --------
    tuple
        (kriging_result, kriging_variance)
    """
    # 對數轉換 (避免負值)
    log_values = np.log1p(values)
    
    # 執行 Kriging
    OK = OrdinaryKriging(
        x_coords, y_coords, log_values,
        variogram_model=variogram_model,
        verbose=False,
        enable_plotting=False
    )
    
    # 建立網格點
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    
    # 執行插值
    z, ss = OK.execute('points', grid_xx.ravel(), grid_yy.ravel())
    
    # 轉換回原始單位
    z_result = np.expm1(z.reshape(grid_xx.shape))
    ss_result = ss.reshape(grid_xx.shape)
    
    # 處理負值
    z_result = np.maximum(z_result, 0)
    
    return z_result, ss_result


def random_forest_interpolation(grid_x, grid_y, x_coords, y_coords, values, 
                          n_estimators=200, min_samples_leaf=3):
    """
    隨機森林插值
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
    n_estimators : int
        樹的數量
    min_samples_leaf : int
        葉節點最小樣本數
        
    Returns:
    --------
    array
        插值結果網格
    """
    # 準備訓練資料
    X = np.column_stack([x_coords, y_coords])
    y = values
    
    # 建立網格點
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    grid_points = np.column_stack([grid_xx.ravel(), grid_yy.ravel()])
    
    # 訓練隨機森林
    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=min_samples_leaf,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X, y)
    
    # 預測
    result = rf.predict(grid_points)
    result = result.reshape(grid_xx.shape)
    
    # 處理負值
    result = np.maximum(result, 0)
    
    return result


def plot_interpolation_comparison(grid_x, grid_y, results, event_name, x_coords, y_coords, values):
    """
    繪製插值結果比較圖
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    results : dict
        插值結果字典
    event_name : str
        事件名稱
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'{event_name} - 插值方法比較', fontsize=16)
    
    methods = ['nearest_neighbor', 'idw', 'kriging', 'random_forest']
    titles = ['Nearest Neighbor', 'IDW', 'Kriging', 'Random Forest']
    
    for i, (method, title) in enumerate(zip(methods, titles)):
        ax = axes[i // 2, i % 2]
        
        result = results[method]
        im = ax.imshow(result, extent=[grid_x.min(), grid_x.max(), grid_y.min(), grid_y.max()],
                   origin='lower', cmap='viridis')
        
        # 添加測站位置
        ax.scatter(x_coords, y_coords, c='red', s=20, alpha=0.7, edgecolors='white')
        
        ax.set_title(f'{title}\\n範圍: {result.min():.1f}-{result.max():.1f} mm')
        ax.set_xlabel('Easting (m)')
        ax.set_ylabel('Northing (m)')
        
        # 添加 colorbar
        plt.colorbar(im, ax=ax, label='雨量 (mm)')
    
    plt.tight_layout()
    
    # 儲存圖片
    output_path = f'outputs/interpolations/{event_name}_interpolation_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 插值比較圖已儲存: {output_path}")


def plot_kriging_rf_difference(grid_x, grid_y, kriging_result, rf_result, event_name):
    """
    繪製 Kriging vs Random Forest 差異圖
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    kriging_result : array
        Kriging 結果
    rf_result : array
        Random Forest 結果
    event_name : str
        事件名稱
    """
    # 計算差異
    difference = kriging_result - rf_result
    
    plt.figure(figsize=(12, 8))
    
    im = plt.imshow(difference, 
                   extent=[grid_x.min(), grid_x.max(), grid_y.min(), grid_y.max()],
                   origin='lower', cmap='RdBu_r', 
                   vmin=-np.max(np.abs(difference)), vmax=np.max(np.abs(difference)))
    
    plt.colorbar(im, label='Kriging - RF (mm)')
    plt.xlabel('Easting (m)')
    plt.ylabel('Northing (m)')
    plt.title(f'{event_name} - Kriging vs Random Forest 差異圖')
    
    # 儲存圖片
    output_path = f'outputs/comparisons/{event_name}_kriging_rf_difference.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"🔄 差異圖已儲存: {output_path}")
    
    return difference


def plot_sigma_map(grid_x, grid_y, kriging_variance, event_name):
    """
    繪製 Sigma Map (Kriging variance)
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    kriging_variance : array
        Kriging 變異數
    event_name : str
        事件名稱
    """
    plt.figure(figsize=(12, 8))
    
    im = plt.imshow(kriging_variance, 
                   extent=[grid_x.min(), grid_x.max(), grid_y.min(), grid_y.max()],
                   origin='lower', cmap='Blues')
    
    plt.colorbar(im, label='預測變異數')
    plt.xlabel('Easting (m)')
    plt.ylabel('Northing (m)')
    plt.title(f'{event_name} - Sigma Map (Kriging 不確定性)')
    
    # 儲存圖片
    output_path = f'outputs/comparisons/{event_name}_sigma_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📈 Sigma Map 已儲存: {output_path}")
    
    return kriging_variance


def save_geotiff(grid_x, grid_y, data, filename, crs='EPSG:3826'):
    """
    儲存為 GeoTIFF 格式
    
    Parameters:
    -----------
    grid_x, grid_y : array
        網格坐標
    data : array
        待儲存資料
    filename : str
        輸出檔名
    crs : str
        坐標系統
    """
    # 計算 transform
    transform = from_bounds(
        grid_x.min(), grid_y.min(), grid_x.max(), grid_y.max(),
        data.shape[1], data.shape[0]
    )
    
    # 儲存 GeoTIFF
    output_path = f'outputs/geotiff/{filename}'
    
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(data, 1)
    
    print(f"🗺️ GeoTIFF 已儲存: {output_path}")


if __name__ == "__main__":
    print("🔧 插值工具函數載入完成")
