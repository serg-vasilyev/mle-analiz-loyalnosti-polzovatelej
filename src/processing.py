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
from pathlib import Path

class DataProcessor:

    def __init__(self):
        self.db = None
        self.project_root = None
        self.tenge_rate_df = None

    # Создаем метод для выгрузки данных из БД и сохранение в csv
    def load_db (self, query, csv_name, folder_name='data'):

        current_file_dir = find_dotenv() 

        # Проверка наличия файла env 
        if not current_file_dir:
            raise FileNotFoundError(
                'файл env в папке проекта отсутствует'
            )

        # Загрузка данных из env       
        load_dotenv(dotenv_path = current_file_dir, override=True)

        
        __db_user = os.getenv('DB_USER')
        __db_pwd = os.getenv('DB_PWD')
        __db_host = os.getenv('DB_HOST')
        __db_port = os.getenv('DB_PORT')
        __db_name = os.getenv('DB_NAME')

        # Проверка на наличие данных в env
        if not all([__db_user, __db_pwd, __db_host, __db_port, __db_name]):
            raise ValueError(
                f'Ошибка: в файле env отсутствуют обязательные данные'
            )

        # Устанавливаем соединение с БД
        connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(
            __db_user,
            __db_pwd,
            __db_host,
            __db_port,
            __db_name,
            ) 

        engine = create_engine(connection_string)
    
        # выгрузка данных из БД с проверкой
        try:
            self.df = pd.read_sql_query(query, con=engine)
        except Exception as e:
            raise RuntimeError(f'Ошибка при выгрузке из БД: {e}')
        finally:
            engine.dispose()

        self.project_root = Path(current_file_dir).parent
        csv_path = self.project_root / folder_name

        # Загрузка бд в файл в папке data
        self.df.to_csv(csv_path / csv_name)

        # load_db(query ='...', csv_name = 'afisha_db.csv') folder_name = 'data' по умолчанию

        # Загрузка файла с курсами валют тенге
    def load_tenge_csv(self, file_name, folder_name = 'data'):
        self.tenge_rate_df = pd.read_csv(f'{self.project_root} / {folder_name} / {file_name}')

    # load_tenge_csv(file_name='final_tickets_tenge_df.csv') folder_name='data' по умолчанию

    def check_data (self):
        
        # Посмотрим на содержимое датасета
        print('Первые 10 строк:')
        print(self.df.head(10))
        print('\nСлучайные 10 строк:')
        print(self.df.sample(10, random_state=42))
        print('\nПоследние 10 строк:')
        print(self.df.tail(10))

        # Выведем основную информацию о датасете
        print(self.df.info())
          
        # выыод на экран таблицы тенге
        print(self.tenge_rate_df)

        # check_data()

    def tenge_conv_merge (self, period_col, tenge_date = 'data'):
        self.period_col = period_col
        self.tenge_date = tenge_date
       
        # Выведем период представленный в датасете для дальнейшей проверки корректности соединения таблиц
        self.df[self.period_col].agg(['min', 'max'])
        
        # Переведем столбец data из типа object в тип datetime
        
        self.tenge_rate_df[tenge_date] = pd.to_datetime(self.tenge_rate_df[tenge_date])

        # Временно соединим датасет с датасетом курса тенге для корректного перевода в рубли, после удалим лишние столбцы
        self.df = pd.merge(self.df, self.tenge_rate_df, left_on=period_col, right_on=tenge_date, how='inner')

        # Проверим соединение
        print('Прверка соединения:')
        print(self.df.info())

        # Проверка корректности периода
        print('проверка периода в новом присоединенном столбце:')
        print(self.df[tenge_date].agg(['min', 'max']))

    # -> tenge_conv_merge(period_col = 'order_dt') tenge_date = 'data' по умолчанию
    
    def tenge_conv_proc (self, new_col, revenue_col, nominal, rate, currency_code, code):
        # Создаем столбец с рублями
        self.df[new_col] = np.where(
            self.df[currency_code] == code,
            (self.df[revenue_col] / self.df[nominal]) * self.df[rate],
            self.df[revenue_col]
            )

        print('весь датасет:')
        print(self.df[[currency_code, revenue_col, new_col]])
        print('валюта kzt:')
        print(self.df[[currency_code, revenue_col, self.period_col, rate, new_col]].loc[self.df[currency_code] == code])

        # Удаление столбцов
        self.df = self.df.drop(columns=[self.tenge_date, nominal, rate, 'cdx'])

        print('Проверка после удаления:')
        print(self.df.info())

        # tenge_conv_proc(new_col='revenue_rub, revenue_col='revenue', nominal='nominal', rate='curs', currency_code='currency_code'. code='kzt')
        
    def nulls(self):    
        
        # подсчет пропусков
        print('Количество пропусков')
        print(self.df.isna().sum())

        print('пропуски в процентах:')
        print((self.df.isna().sum() / self.df.shape[0] * 100).round(2))

        # nulls()

    def optimization (self, cols_int, cols_float):
        #оптимизируем столбцы с целочисленными значениями
        for col in cols_int:
            self.df[col] = pd.to_numeric(df[col], downcast = 'integer')

        # оптимизируем столбец 'days_since_prev'  
        for col in cols_float:
            self.df[col] = pd.to_numeric(df[col], downcast = 'float')

        print('Проверка оптимизации:')
        print(self.df.info())

        # optimization(cols_int = ['order_id', 'tickets_count', 'event_id'], cols_float = ['days_since_prev'] )
        
    def duplicates_check (self, cols, keep='first'):

        # проверим на дубликаты датафрейм
        print(f'Дубликаты в датафрейме: {self.df.duplicated().sum()}')
        
        # проверим столбец order_id на дубликаты
        print(f'''\nЯвные/неявные дубликаты в столбце/столбцах {cols}: 
            {self.df.duplicated(subset=cols, 
                                keep=keep)
                                .sum()
            }'''
            )

        # duplicates_check (cols=["order_id", "service_name"])

    def lower_register (self, cols):

        # приведем к нижнему регистру 'service_name', 'region_name', 'city_name'
        for col in cols:
            self.df[col] = self.df[col].str.lower()

        # lower_register(cols=['service_name', 'region_name', 'city_name'])

    def show_duplicates (self, cols, keep='first', sort_cols=None, ascending=True):
        # Выведем эти строки
        print('\nЯвные/неявные дубликаты в столбце/столбцах {cols}:')
        pd.set_option('display.max_rows', None)
        duplicated_df = self.df[self.df.duplicated(
            subset=cols, 
            keep=keep
            )]

        if sort_cols is not None:
            return duplicated_df.sort_values(sort_cols, ascending=ascending)
        print(duplicated_df)
        return duplicated_df
        
    def delete_duplicates (self, cols, sort_cols=None, ascending=True, keep='first'):
        #Зафиксируем начальное количество строк
        self.rows_before = self.df.shape[0]

        # Удаляем дубликаты
        self.df = (
            self.df.sort_values(by='days_since_prev', ascending=False)
            .drop_duplicates(
            subset=["user_id", "order_ts", "revenue", "event_id", "tickets_count"], 
            keep='first'
            ).sort_index()
            )

        df_processed = self.df

        if sort_cols is not None:
            df_processed = df_processed.sort_values(by=sort_cols, ascending=ascending)
        df_processed = df_processed.drop_duplicates(
            subset=cols,
            keep=keep
        )

        if sort_cols is not None:
            df_processed = df_processed.sort_index()

        self.df = df_processed

        #Посчитаем сколько строк удалено
        print(f'Количество удаленных строк: {rows_before - self.df.shape[0]}')
        print(f'Количество удаленных строк в процентах: {((rows_before - self.df.shape[0]) / rows_before):.2%}')

    def obj_info (self, cols=None, cols_top_tail=None):       
        
        # посмотрим на категориальные столбцы
        self.df.describe(include='object')

        # Проверка количества значенний в данных
        if cols is not None:
            for col in cols:
                print(f'количество {col}:')
                print(self.df[col].value_counts())

        if cols_top_tail is not None:
            for col in cols_top_tail:
                print(f'топ 10 {col}:')
                print(self.df[col].value_counts().head(10))
                print(f'последние 5 {col}:')
                print(self.df[col].value_counts().tail(5))

    def fig_info (self, cols, sub_plot_size, edgecolor='white', color='skyblue'):
        
        # Теперь посмотрим на числовые значения и проверим выбросы, с построением гистограмм и боксплотов
        self.df.describe()

        fig, axes = plt.subplots(sub_plot_size, figsize=(14, 22), constrained_layout=True)

        for i, (name, values) in enumerate(self.df[cols].items()):
            hist_idx = 2 * i
            box_idx = 2 * i + 1
    
            sns.histplot(data=self.df, 
                x=name, 
                bins=60, 
                kde=True, 
                ax=axes[hist_idx], 
                edgecolor=edgecolor, 
                color=color
                )
    
            axes[hist_idx].set_title(f'Гистограмма для {name}')
            axes[hist_idx].set_ylabel('Частота')
            axes[hist_idx].grid(axis='y')
    
            sns.boxplot(data=self.df, y=name, ax=axes[box_idx])
            axes[box_idx].set_title(f'Boxplot для {name}')
            axes[box_idx].grid(axis='y')
    
        plt.suptitle(f'Распределение данных в столбцах {cols}')
        plt.show()

    def filtration (self,cols, quant):    

        # Зафиксируем количество строк до фильтрации
        len_before_filt = self.df.shape[0]

        #Отфильтруем столбец revenue_rub по 99 процентилю
        quantile_quant = self.df[cols].quantile(quant)
        self.df = self.df.loc[self.df[cols] <= quantile_quant]

        print(f'Отфильтровано: {len_before_filt - self.df.shape[0]}')
        print(f'в процентах: {((len_before_filt - self.df.shape[0]) / len_before_filt):.2%}')

    def bar_plot (self, col, edgecolor='white', color='skyblue')
        plt.figure(figsize = (14,6))
        self.df[col].value_counts().plot(kind='bar', 
                                        x=col, 
                                        rot=0, 
                                        edgecolor=edgecolor, 
                                        color=color
                                        )
    
        plt.title(f'Распределение данных в столбце {col}')
        plt.xlabel({col})
        plt.ylabel('частота')
        plt.grid(axis='y')
        plt.show()

    def neg_revenue_info (self, col):
        
        # разберемся с отрицательной выручкой
        print(f'Количество отрицательной и нулевой выручки: {self.df.loc[df[col] <= 0].shape[0]}')
        print(f'в процентах: {((self.df.loc[df[col] <= 0].shape[0]) / df.shape[0]):.4%}')

    def neg_revenue_filt (self, col):    
        self.df = self.df.loc[df[col] > 0]
        print(f'количество удаленных строк включая дубликаты: {self.rows_before - self.df.shape[0]}')
        print(f'количество удаленных строк в процентах: {((self.rows_before - self.df.shape[0]) / self.rows_before):.4%}')

    def cnt_df_after_filt (self)
        print(f'Количество строк в предобработанном датафрейме: {self.df.shape[0]}')