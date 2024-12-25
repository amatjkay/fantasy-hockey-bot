from datetime import datetime, timedelta
from src.config.settings import ESPN_TIMEZONE

def get_previous_week_dates():
    """Получение дат предыдущей недели
    
    Returns:
        tuple: (начало_недели, конец_недели) в формате datetime с timezone
    """
    espn_now = datetime.now(ESPN_TIMEZONE)
    days_since_tuesday = (espn_now.weekday() - 1) % 7
    current_tuesday = espn_now - timedelta(days=days_since_tuesday)
    current_tuesday = current_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    previous_tuesday = current_tuesday - timedelta(days=7)
    previous_monday = previous_tuesday + timedelta(days=6)
    previous_monday = previous_monday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return previous_tuesday, previous_monday

def get_week_key(start_date, end_date):
    """Создание ключа недели из дат
    
    Args:
        start_date (datetime): Дата начала недели
        end_date (datetime): Дата конца недели
        
    Returns:
        str: Ключ недели в формате 'YYYY-MM-DD_YYYY-MM-DD'
    """
    return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

def format_date_range(week_key):
    """Форматирование диапазона дат для отображения
    
    Args:
        week_key (str): Ключ недели в формате 'YYYY-MM-DD_YYYY-MM-DD'
        
    Returns:
        str: Отформатированный диапазон дат
    """
    start_date, end_date = week_key.split('_')
    return f"{start_date} - {end_date}"
