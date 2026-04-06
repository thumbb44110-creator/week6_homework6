"""
Variogram 分析工具函數
"""

import numpy as np
import matplotlib.pyplot as plt
from pykrige.ok import OrdinaryKriging
from pykrige.variogram import variogram_estimate
from sklearn.metrics import mean_squared_error


def calculate_experimental_variogram(x_coords, y_coords, values, max_lag=None, n_lags=15):
    """
    計算實驗性 variogram
    
    Parameters:
    -----------
    x_coords, y_coords : array
        測站坐標
    values : array
        觀測值
    max_lag : float
        最大滯後距離
    n_lags : int
        滯後數量
        
    Returns:
    --------
    tuple
        (lags, variogram_values)
    """
    # 計算最大距離
    distances = np.sqrt((x_coords[:, np.newaxis] - x_coords)**2 + 
                    (y_coords[:, np.newaxis] - y_coords)**2)
    
    if max_lag is None:
        max_lag = np.max(distances) * 0.5
    
    # 使用 pykrige 的 variogram_estimate
    lags, variogram_values = variogram_estimate(
        x_coords, y_coords, values, 
        lag_dist=max_lag/n_lags, 
        n_lags=n_lags
    )
    
    return lags, variogram_values


def fit_variogram_models(lags, variogram_values):
    """
    擬合多種 variogram 模型
    
    Parameters:
    -----------
    lags : array
        滯後距離
    variogram_values : array
        variogram 值
        
    Returns:
    --------
    dict
        擬合結果字典
    """
    models = {}
    
    # Spherical 模型
    spherical_params = fit_spherical_model(lags, variogram_values)
    models['spherical'] = {
        'params': spherical_params,
        'model_func': spherical_variogram,
        'name': 'Spherical'
    }
    
    # Exponential 模型
    exponential_params = fit_exponential_model(lags, variogram_values)
    models['exponential'] = {
        'params': exponential_params,
        'model_func': exponential_variogram,
        'name': 'Exponential'
    }
    
    return models


def fit_spherical_model(lags, variogram_values):
    """
    擬合 Spherical 模型
    """
    # 使用最小二乘法擬合
    from scipy.optimize import curve_fit
    
    def spherical_func(h, sill, range_, nugget):
        return spherical_variogram(h, sill, range_, nugget)
    
    # 初始參數估計
    initial_sill = np.max(variogram_values)
    initial_range = np.max(lags) * 0.5
    initial_nugget = variogram_values[0] if len(variogram_values) > 0 else 0
    
    try:
        params, _ = curve_fit(
            spherical_func, lags, variogram_values,
            p0=[initial_sill, initial_range, initial_nugget],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf])
        )
        return params
    except:
        return [initial_sill, initial_range, initial_nugget]


def fit_exponential_model(lags, variogram_values):
    """
    擬合 Exponential 模型
    """
    from scipy.optimize import curve_fit
    
    def exponential_func(h, sill, range_, nugget):
        return exponential_variogram(h, sill, range_, nugget)
    
    # 初始參數估計
    initial_sill = np.max(variogram_values)
    initial_range = np.max(lags) * 0.3
    initial_nugget = variogram_values[0] if len(variogram_values) > 0 else 0
    
    try:
        params, _ = curve_fit(
            exponential_func, lags, variogram_values,
            p0=[initial_sill, initial_range, initial_nugget],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf])
        )
        return params
    except:
        return [initial_sill, initial_range, initial_nugget]


def spherical_variogram(h, sill, range_, nugget):
    """
    Spherical variogram 模型
    """
    h = np.array(h)
    result = np.zeros_like(h)
    
    mask = h <= range_
    result[mask] = nugget + sill * (1.5 * (h[mask] / range_) - 0.5 * (h[mask] / range_)**3)
    
    mask = h > range_
    result[mask] = nugget + sill
    
    return result


def exponential_variogram(h, sill, range_, nugget):
    """
    Exponential variogram 模型
    """
    h = np.array(h)
    return nugget + sill * (1 - np.exp(-3 * h / range_))


def plot_variogram_comparison(lags, experimental, models, event_name):
    """
    繪製 variogram 比較圖
    
    Parameters:
    -----------
    lags : array
        滯後距離
    experimental : array
        實驗性 variogram
    models : dict
        擬合模型字典
    event_name : str
        事件名稱
    """
    plt.figure(figsize=(10, 6))
    
    # 繪製實驗點
    plt.scatter(lags, experimental, c='red', s=30, alpha=0.7, label='實驗點')
    
    # 繪製擬合模型
    h_smooth = np.linspace(0, np.max(lags), 100)
    
    for model_name, model_info in models.items():
        params = model_info['params']
        model_func = model_info['model_func']
        fitted_values = model_func(h_smooth, *params)
        
        plt.plot(h_smooth, fitted_values, linewidth=2, 
                label=f"{model_info['name']} (Sill={params[0]:.2f}, Range={params[1]:.0f}m, Nugget={params[2]:.2f})")
    
    plt.xlabel('距離 (m)')
    plt.ylabel('Variogram')
    plt.title(f'{event_name} - Variogram 模型比較')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 儲存圖片
    output_path = f'outputs/variograms/{event_name}_variogram_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📈 Variogram 圖已儲存: {output_path}")
    
    return models


def select_best_model(models, experimental, lags):
    """
    選擇最佳 variogram 模型
    
    Parameters:
    -----------
    models : dict
        擬合模型字典
    experimental : array
        實驗性 variogram
    lags : array
        滯後距離
        
    Returns:
    --------
    tuple
        (best_model_name, best_model_info, mse_scores)
    """
    mse_scores = {}
    
    for model_name, model_info in models.items():
        params = model_info['params']
        model_func = model_info['model_func']
        
        # 計算擬合值
        fitted_values = model_func(lags, *params)
        
        # 計算 MSE
        mse = mean_squared_error(experimental, fitted_values)
        mse_scores[model_name] = mse
    
    # 選擇 MSE 最小的模型
    best_model_name = min(mse_scores, key=mse_scores.get)
    best_model_info = models[best_model_name]
    
    print(f"🏆 最佳模型: {best_model_name} (MSE: {mse_scores[best_model_name]:.4f})")
    
    return best_model_name, best_model_info, mse_scores


if __name__ == "__main__":
    print("📐 Variogram 分析工具函數載入完成")
