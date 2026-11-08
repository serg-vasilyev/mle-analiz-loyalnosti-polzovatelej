# Импортируем библиотеки
import pandas as pd
import numpy as np

# Загружаем библиотеки для визуализации данных
import matplotlib.pyplot as plt
import seaborn as sns

# Загружаем библиотеку для расчёта коэффициента корреляции phi_k
from phik import phik_matrix

# Загружаем библиотеку для выгрузки sql БД
from sqlalchemy import create_engine 

# Для чтения данных из env файла
import os
from dotenv import load_dotenv, find_dotenv

class DataProcessor:

    def __init__(self, include_all=False, timeout: int = 30):
        self.include_all = include_all
        self.timeout = timeout

    def __load_db__ (self):

        current_file_dir = find_dotenv() 

        if not current_file_dir:
            raise FileNotFoundError(
                'файл env в папке проекта отсутствует'
            )
       
        load_dotenv(dotenv_path = current_file_dir, override=True)

        
        db_user = os.getenv('DB_USER')
        db_pwd = os.getenv('DB_PWD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        
        if not all([db_user, db_pwd, db_host, db_port, db_name]):
            raise ValueError(
                f'Ошибка: в файле env отсутствуют обязательные данные'
            )

        
          
