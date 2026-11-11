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
        self.user_profile = None

    # Создаем метод для выгрузки данных из БД и сохранение в csv
    # с сохранением в папку пользователя, по умолчанию 'data'
    
    def load_db(self, query, csv_name, folder_name='data'):

        current_file_dir = find_dotenv()

        # Проверка наличия файла env
    
        if not current_file_dir:
            raise FileNotFoundError(
                'файл env в папке проекта отсутствует'
            )

        # Загрузка данных из env
    
        load_dotenv(dotenv_path=current_file_dir, override=True)

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

    # вызов load_db(query ='...', csv_name = 'afisha_db.csv') 

    # Загрузка файла с курсами валют тенге
    # folder_name='data' по умолчанию
    
    def load_tenge_csv(self, file_name, folder_name='data'):
        self.tenge_rate_df = pd.read_csv(
            f'{self.project_root}/{folder_name}/{file_name}'
        )

    # вызов load_tenge_csv(file_name='final_tickets_tenge_df.csv') 

    # Метод для первого знвкомства с данными
    
    def check_data(self):

        # Посмотрим на содержимое датасета
    
        print('Первые 10 строк:')
        print(self.df.head(10))
        print('\nСлучайные 10 строк:')
        print(self.df.sample(10, random_state=42))
        print('\nПоследние 10 строк:')
        print(self.df.tail(10))

        # Выведем основную информацию о датасете
    
        print('\nИнформация по датасету:')
        print(self.df.info())

        # выыод на экран таблицы тенге
    
        print('\nИнформация по таблице с тенге:')
        print(self.tenge_rate_df)

    # вызов check_data()
    
    # Метод для соединения таблиц и проверки соединения
    # tenge_date = 'data' по умолчанию
    
    def tenge_conv_merge(self, period_col, tenge_date='data'):
        self.period_col = period_col
        self.tenge_date = tenge_date

        # Выведем период представленный в датасете для дальнейшей проверки корректности соединения таблиц
    
        self.df[self.period_col].agg(['min', 'max'])

        # Переведем столбец data из типа object в тип datetime
    
        self.tenge_rate_df[tenge_date] = pd.to_datetime(
            self.tenge_rate_df[tenge_date]
        )

        # Временно соединим датасет с датасетом курса тенге для корректного перевода в рубли, после удалим лишние столбцы
    
        self.df = pd.merge(
            self.df, self.tenge_rate_df,
            left_on=period_col, right_on=tenge_date, how='inner'
        )

        # Проверим соединение
    
        print('\nПрверка соединения:')
        print(self.df.info())

        # Проверка корректности периода
    
        print('\nпроверка периода в новом присоединенном столбце:')
        print(self.df[tenge_date].agg(['min', 'max']))

    # вызов tenge_conv_merge(period_col = 'order_dt') 

    # Метод для конвертации валют 
    # с созданием нового столбца для валюты рубли
    # и вывод результата для проверки
    
    def tenge_conv_proc(
            self,
            new_col,
            revenue_col,
            nominal, 
            rate,
            currency_code,
            code
    ):

        # Создаем столбец с рублями
    
        self.df[new_col] = np.where(
            self.df[currency_code] == code,
            (self.df[revenue_col] / self.df[nominal]) * self.df[rate],
            self.df[revenue_col]
        )

        print('\nвесь датасет после конвертации:')
        print(self.df[[currency_code, revenue_col, new_col]])
        print('\nвалюта kzt:')
        print(
            self.df[[currency_code, revenue_col, self.period_col,
                     rate, new_col]].loc[self.df[currency_code] == code]
        )

    # вызов tenge_conv_proc(
    #         new_col='revenue_rub',
    #         revenue_col='revenue',
    #         nominal='nominal',
    #         rate='curs',
    #         currency_code='currency_code',
    #         code='kzt'
    #     )


    # Удаление лишних столбцов и вывод для прверки корректности удаления 
    
    def del_cols(self, del_cols):

        # Удаление столбцов
    
        self.df = self.df.drop(columns=del_cols)

        print('\nПроверка после удаления:')
        print(self.df.info())

    # вызов del_cols(del_cols=['data', 'nominal', 'curs', 'cdx' ])
    
    
    # Метод для поиска пропусков
    
    def nulls(self):

        # подсчет пропусков
    
        print('\nКоличество пропусков')
        print(self.df.isna().sum())

        print('\nпропуски в процентах:')
        print((self.df.isna().sum() / self.df.shape[0] * 100).round(2))

    # вызов nulls()

    # Метод для оптимизации разрядности данных.
    # по умолчанию cols_int=None, cols_float=None
    
    def optimization(self, cols_int=None, cols_float=None):

        # оптимизируем столбцы с целочисленными значениями
    
        if cols_int is not None:
            for col in cols_int:
                self.df[col] = pd.to_numeric(self.df[col], downcast='integer')
        
        # оптимизируем столбец float
    
        if cols_float is not None:
           for col in cols_float:
                self.df[col] = pd.to_numeric(self.df[col], downcast='float')

        print('\nПроверка оптимизации:')
        print(self.df.info())

    # вызов optimization(
    #           cols_int=['order_id', 'tickets_count', 'event_id'],
    #           cols_float=['days_since_prev']
    # )

    # Метод для проверки дубликатов, по умолчанию keep='first' - первое вхождение не дубликат 

    def duplicates_check(self, cols, keep='first'):

        # проверим на дубликаты датафрейм

        print(f'\nДубликаты в датафрейме: {self.df.duplicated().sum()}')

        # проверка конкретного столбца или список столбцов 

        print(
            f'\nЯвные/неявные дубликаты в столбце/столбцах {cols}: {self.df.duplicated(subset=cols, keep=keep).sum()}'
        )

    # вызов duplicates_check (cols=["order_id", "service_name"])

    # Метод для перевода строк в нижний регистр

    def lower_register(self, cols):

        # приводим столбцы к нижнему регистру

        for col in cols:
            self.df[col] = self.df[col].str.lower()

        print(f'\nпосле нормализации:')

    # вызов lower_register(cols=['service_name', 'region_name', 'city_name'])

    # метод для вывода данных по дубликатам
    # по умолчанию keep='first', sort_cols=None, ascending=True

    def show_duplicates(
            self,
            cols,
            keep='first',
            sort_cols=None,
            ascending=True
    ):

        # Выведем строки

        print(f'\nЯвные/неявные дубликаты в столбце/столбцах {cols}:')
        pd.set_option('display.max_rows', None)
        duplicated_df = self.df[self.df.duplicated(
            subset=cols,
            keep=keep)
        ]

        # Проверка sort_cols на None

        if sort_cols is not None:
            duplicated_df.sort_values(sort_cols, ascending=ascending)
        print(duplicated_df)
        return duplicated_df

    # вызов process.show_duplicates(
    #         cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
    #         keep=False, sort_cols='user_id')

    # Метод удаляет дубликаты и выводит колиство и долю удаленных строк
    # По умолчанию sort_cols=None, ascending=True, keep='first'

    def delete_duplicates(
            self,
            cols,
            sort_cols=None,
            ascending=True,
            keep='first'):

        # Зафиксируем начальное количество строк

        self.rows_before = self.df.shape[0]

        # Удаляем дубликаты

        df_processed = self.df

        # Проверка sort_cols на None

        if sort_cols is not None:
            df_processed = df_processed.sort_values(
                by=sort_cols, ascending=ascending)

        # Удаление дубликатов

        df_processed = df_processed.drop_duplicates(
            subset=cols,
            keep=keep
        )

        # Возврат сортировки по индексу

        if sort_cols is not None:
            df_processed = df_processed.sort_index()

        self.df = df_processed

        # Посчитаем сколько строк удалено

        print(
            f'\nКоличество удаленных строк: {self.rows_before - self.df.shape[0]}'
        )
        print(
            f'\nКоличество удаленных строк в процентах: {((self.rows_before - self.df.shape[0]) / self.rows_before):.2%}'
        )

    # вызов delete_duplicates(
    #     cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
    #     sort_cols='days_since_prev',
    #     ascending=False)

    
    # Метод выводит информацию по столбцам типа obj
    # по умолчанию cols=None, cols_top_tail=None

    def obj_info(self, cols=None, cols_top_tail=None):

        # посмотрим на категориальные столбцы

        self.df.describe(include='object')

        # Проверка количества значенний в данных

        if cols is not None:
            for col in cols:
                print(f'\nколичество {col}:')
                print(self.df[col].value_counts())
                print()

        if cols_top_tail is not None:
            for col in cols_top_tail:
                print(f'\nтоп 10 {col}:')
                print(self.df[col].value_counts().head(10))
                print()
                print(f'\nпоследние 5 {col}:')
                print(self.df[col].value_counts().tail(5))
                print()

    # вызов obj_info(
    #         cols=['device_type_canonical', 'event_type_main'],
    #         cols_top_tail=['user_id', 'event_name',
    #                        'service_name', 'region_name', 'city_name']

    # Вывод информации по числовым данным включая гистограммы и боксплоты
    # По умолчанию edgecolor='white', color='skyblue' для графиков

    def fig_info(self, cols, edgecolor='white', color='skyblue'):

        # перевод строки в список, 
        # на случай передачи названия одного столбца в виде строки

        if isinstance(cols, str):
            cols = [cols]

        print('\nИнформация по числовым столбцам:')
        print(self.df.describe())

        # построение гистограмм и боксплотов для каждого переданного столбца

        for name in cols:
            fig, (ax_hist, ax_box) = plt.subplots(
                1, 2, figsize=(14, 6), constrained_layout=True
            )

            sns.histplot(data=self.df,
                         x=name,
                         bins=60,
                         kde=True,
                         ax=ax_hist,
                         edgecolor=edgecolor,
                         color=color
                         )

            ax_hist.set_title(f'Гистограмма для {name}')
            ax_hist.set_ylabel('Частота')
            ax_hist.grid(axis='y')

            sns.boxplot(data=self.df, y=name, ax=ax_box, color=color)
            ax_box.set_title(f'Boxplot для {name}')
            ax_box.grid(axis='y')

        plt.suptitle(f'\nРаспределение данных в столбцах {cols}')
        plt.show()

    # вызов fig_info(cols=['tickets_count', 'days_since_prev', 'revenue_rub'])

    # Метод для фильтрации по квантилю с 
    # выводом количества отфильтрованных строк

    def filtration(self, cols, quant):

        # Зафиксируем количество строк до фильтрации

        len_before_filt = self.df.shape[0]

        # Фильтрация

        quantile_quant = self.df[cols].quantile(quant)
        self.df = self.df.loc[self.df[cols] <= quantile_quant]

        print(
            f'\nОтфильтровано по {quant} квантилю: {len_before_filt - self.df.shape[0]}')
        print(
            f'\nв процентах: {((len_before_filt - self.df.shape[0]) / len_before_filt):.2%}')

    # вызов filtration(cols='revenue_rub', quant=0.99)

    # Метод для вызова matplot столбчатых диаграмм. 
    # По умолчанию edgecolor='white', color='skyblue' для графиков

    def bar_plot(self, col, edgecolor='white', color='skyblue'):
        plt.figure(figsize=(14, 6))

        self.df[col].value_counts().plot(
            kind='bar',
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

    # вызов bar_plot(col='tickets_count')

    # Метод для поиска отрицательных и равных нулю значений 
    # с выводом количества и доли

    def neg_revenue_info(self, col):

        # разберемся с отрицательной выручкой

        print(
            f'\nКоличество отрицательной и нулевой выручки: {self.df.loc[self.df[col] <= 0].shape[0]}'
        )
        print(
            f'\nв процентах: {((self.df.loc[self.df[col] <= 0].shape[0]) / self.df.shape[0]):.4%}'
        )

    # вызов neg_revenue_info(col='revenue_rub')

    # Метод для фильтрации по отрицательным значениям 
    # с выводом количества и доли отфильтрованных строк

    def neg_revenue_filt(self, col):
        self.df = self.df.loc[self.df[col] > 0]
        print(
            f'\nколичество удаленных строк включая дубликаты: {self.rows_before - self.df.shape[0]}'
        )
        print(
            f'\nколичество удаленных строк в процентах: {((self.rows_before - self.df.shape[0]) / self.rows_before):.4%}'
        )

    # вызов neg_revenue_filt(col='revenue_rub')

    # Метод для вывода количества строк в предобработаном датафрейме

    def cnt_df_after_filt(self):
        print(
            f'\nКоличество строк в предобработанном датафрейме: {self.df.shape[0]}'
        )
    
    # вызов cnt_df_after_filt()

# СОЗДАНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ

    # Метод для создания профиля пользователя 
    # с возможностью самому именовать столбцы, 
    # выбирать столбцы для агрегации и функций агрегации 
    # и добавлять новый бинарный столбец
    # По умолчанию binary_col_name=None на случай, если бинарный столбец не нужен
    
    def user_profile_create(
            self,
            sort_cols,
            group_cols,
            col_for_binary,
            binary_col_name=None,
            **kwargs
    ):

        # Сортируем датафрейм
    
        df_sorted = self.df.sort_values(sort_cols)

        # Создаем профиль
    
        self.user_profile = df_sorted.groupby(group_cols).agg(
            **{name: (col, op) for name, (col, op) in kwargs.items()}
        )

        # Добавляем бинарный столбец
    
        if binary_col_name is not None:
            self.user_profile[binary_col_name] = (
                self.user_profile[col_for_binary] >= 2
                ).astype(int)

        print('\nПрофиль пользователя:')
        print(self.user_profile.head(10))
    
    # вызов process.user_profile_create(
    #         sort_cols='order_ts',
    #         group_cols='user_id',
    #         binary_col_name='is_two',
    #         col_for_binary='total_orders',
    #         first_order=('order_dt', 'min'),
    #         last_order=('order_dt', 'max'),
    #         first_device=('device_type_canonical', 'first'),
    #         first_region=('region_name', 'first'),
    #         first_event_type=('event_type_main', 'first'),
    #         total_orders=('order_id', 'count'),
    #         avg_revenue=('revenue_rub', 'mean'),
    #         avg_time_between_orders=('days_since_prev', 'mean')
    #     )

    # Поиск аномалий
    
    def anomaly_check(self, mean_col, binary_col, info_cols):

        print(
            f'\nобщее число пользователей в выборке: {self.user_profile.shape[0]}'
        )
        print(
            f'\nсредняя выручка с одного заказа: {self.user_profile[mean_col].mean(): .2f}'
        )
        print(
            f'\nдоля пользователей, совершивших 2 и более заказа: {self.user_profile[binary_col].mean(): .2%}'
        )

        print(f'\nСтатистические показатели {info_cols}:')
        print(self.user_profile[info_cols].describe())
    
    # вызов process.anomaly_check(
    #         mean_col='avg_revenue',
    #         binary_col='is_two',
    #         info_cols=['total_orders', 'avg_time_between_orders']

    # гиcтограммы и боксплоты для статистических данных 
    # По умолчанию edgecolor='white', color='skyblue'
    
    def analytic_hist_box_plot(self, cols, edgecolor='white', color='skyblue'):
        if isinstance(cols, str):
            cols = [cols]

        for name in cols:
            fig, (ax_hist, ax_box) = plt.subplots(
                1, 2, figsize=(14, 6), constrained_layout=True
            )

            sns.histplot(
                data=self.user_profile,
                x=name,
                bins=60,
                kde=True,
                ax=ax_hist,
                edgecolor=edgecolor,
                color=color
            )

            ax_hist.set_title(f'Гистограмма для {name}')
            ax_hist.set_ylabel('Частота')
            ax_hist.grid(axis='y')

            sns.boxplot(data=self.user_profile, y=name, ax=ax_box, color=color)
            ax_box.set_title(f'Boxplot для {name}')
            ax_box.grid(axis='y')

        plt.suptitle(f'\nРаспределение данных в столбцах {cols}')
        plt.show()
    
    # вызов analytic_hist_box_plot(
    #     cols=['total_orders', 'avg_time_between_orders']

    # Проверка количества строк для удаления по столбцам и квантилям на выбор пользователя
    # По умолчанию cols=None, quants=None
    
    def analytic_before_filt_check(self, cols=None, quants=None):
        cols = cols or []
        quants = quants or []

        if not cols or not quants:
            print('\nНе указаны столбцы или квантили для расчета')

        # Зафиксируем количество строк до фильтрации
    
        self.user_before = self.user_profile.shape[0]
        print(
            f'\nКоличество строк до фильтрации df user_profile: {self.user_before}'
        )

        # Перебор квантилей и колонок для расчетов, вывод того, что доступно
    
        for q_val in quants:
            print(f'\n---Расчет для квантиля {q_val} ---')

            for col_name in cols:
                if col_name is None:
                    continue
                quant_calc = self.user_profile[col_name].quantile(q_val)
                print(f'{q_val} квантиль для {col_name}: {quant_calc}')

                to_del = self.user_profile.loc[self.user_profile[col_name] >= quant_calc]
                del_count = to_del.shape[0]
                print(
                    f'\nколичество строк более {q_val} для {col_name}: {del_count}'
                )

                del_share = del_count / self.user_before
                print(
                    f'\nДоля строк по {col_name} для удаления: {del_share: .2%}'
                )
                print()
    
    # вызов analytic_before_filt_check(
    #     cols=['total_orders', 'avg_time_between_orders'],
    #     quants=[0.99, 0.95]

    # Фильтрация по квантилям с выводом количества, доли отфильтрованных строк 
    # и статистических данных после фильтрации для сравнения изменений  
    
    def analytic_filt(self, cols, quant):
        quantiles = self.user_profile[cols].quantile(quant)

        final_mask = pd.Series(True, index=self.user_profile.index)

        for col in cols:
            q_val = quantiles[col]
            mask = self.user_profile[col] <= q_val
            if col == 'avg_time_between_orders':
                mask = mask | self.user_profile[col].isna()

            final_mask &= mask

        self.user_profile = self.user_profile.loc[final_mask]

        print(
            f'\nколичество отфильтрованных строк: {self.user_before - self.user_profile.shape[0]}'
        )
        print(
            f'\nДоля отфильтрованных строк: {((self.user_before - self.user_profile.shape[0]) / self.user_before): .2%}'
        )
        print()

        # изменение после фильтрации
    
        print('\nизменения после филбтрации:')
        print(self.user_profile.describe())
        print()
    
    # вызов analytic_filt(
    #     cols=['total_orders', 'avg_time_between_orders'], quant=0.99
    # )


# ИССЛЕДОВАТЕЛЬСКИЙ АНАЛИХ ДАННЫХ

    # Распределение пользователей по различным признакам 
    
    def users_by_cat(self, cols):
        for col in cols:
            print(f'\nКоличество пользователей по {col}:')
            print(self.user_profile[col].value_counts())
            print(f'\nДоля пользователей по {col}:')
            print((self.user_profile[col].value_counts(
            ) / self.user_profile.shape[0] * 100).round(4))
    
    # вызов users_by_cat(
    #     cols=['first_event_type', 'first_device', 'first_region']

    # вывод столбчатых диаграмм для соответствующих данных. 
    # По умолчанию edgecolor='black'
    
    def user_cat_bar_plot(self, cols, edgecolor='black'):
        if isinstance(cols, str):
            cols = [cols]

        for name in cols:
            plt.figure(figsize=(14, 6), constrained_layout=True)
            counts = self.user_profile[name].value_counts().head(10)

            sns.barplot(
                x=counts.index,
                y=counts.values,
                hue=counts.index,
                legend=False,
                edgecolor=edgecolor
            )

            plt.title(f'Распределение по {name}')
            plt.xlabel(name)
            plt.ylabel('количество пользователей')
            plt.tick_params(axis='x', labelrotation=45)
            plt.grid(axis='y'),
            plt.show()
    
    # вызов user_cat_bar_plot(
    #     cols=['first_event_type', 'first_device', 'first_region']

    # Метод для расчета количества и долей распределения 
    # по бинарному признаку с построением столбчатых диаграмм 
    # и линии общей средней бинарного признака по всем данным. 
    # По умолчанию edgecolor='black', linecolor='magenta', linestyle='--',linewidth=2
    
    def return_analysis(
            self,
            binary_col,
            cat_cols,
            cnt_col,
            edgecolor='black',
            linecolor='magenta',
            linestyle='--',
            linewidth=2
    ):

        # Посчитаем долю долю пользователей, совершивших два и более заказа для каждого сегмента.
    
        print(
            f'\nколичество пользователей, совершивших два и более заказа: {self.user_profile[binary_col].sum()}'
        )
        print(
            f'\nДоля пользователей, совершивших два и более заказа: {self.user_profile[binary_col].mean():.2%}'
        )

        # Напишем цикл для подсчета долей по сегментам
    
        for col in cat_cols:
            print(
                f'\nДоля пользователей, совершивших два и более заказа по {col}:')
            print(
                (
                    self.user_profile.groupby(col)[binary_col]
                    .agg(count='count', mean=lambda x: x.mean() * 100)
                )
                .round(4)
                .sort_values(by='count', ascending=False)
            )

        # Сразу создаем графики
        # перевод в список, если одиночный столбец передан как строка
    
        if isinstance(cat_cols, str):
            cat_cols = [cat_cols]

        for name in cat_cols:
            plt.figure(figsize=(14, 6), constrained_layout=True)

            user_share = round((self.user_profile[binary_col].mean() * 100), 4)

            # Считаем доли по сегментам
    
            user_profile_groupped = (
                self.user_profile.groupby(name)[binary_col]
                .agg(share=lambda x: x.mean() * 100, count='count')
                .round(4)
                .reset_index()
            )

            # условие сортировки по count, на случай если необходимо, 
            # как в случае с регионами
    
            if name == cnt_col:
                user_profile_groupped = user_profile_groupped.sort_values(
                    by='count', ascending=False).head(10)
            else:
                user_profile_groupped = user_profile_groupped.sort_values(
                    by='share', ascending=False)

            sns.barplot(
                data=user_profile_groupped,
                x=name,
                y='share',
                hue=name,
                legend=False,
                edgecolor=edgecolor
            )

            # Построение линии с общей долей
    
            plt.axhline(
                user_share,
                color=linecolor,
                linestyle=linestyle,
                linewidth=linewidth,
                label=f'общая доля пользователей {user_share}'
            )

            # Настраиваем графики
    
            plt.title(f'\nДоля пользователей по {name}')
            plt.xlabel(f'{name}')
            plt.ylabel('\nДоля пользователей (%)')
            plt.legend(loc='upper right')

            if name == 'first_region':
                plt.tick_params(axis='x', labelrotation=45)

            plt.grid(axis='y')
            plt.show()
    
    # вызов process.return_analysis(
    #         binary_col='is_two',
    #         cat_cols=['first_event_type', 'first_device', 'first_region'],
    #         cnt_col='first_region'
    #     )

# Проверка продуктовых гипотез

    # Гипотеза 1
    # Сравнение регионов
    
    def compare_type(self, col, binary_col, name_1, name_2):
        sport_users = self.user_profile.loc[self.user_profile[col]
                                            == name_1][binary_col].mean()
        concert_users = self.user_profile.loc[self.user_profile[col] == name_2][binary_col].mean(
        )

        compare = name_1 if sport_users > concert_users else name_2 if concert_users > sport_users else 'равны'
        print(f'''\nДоля возвратов {name_1}: {sport_users: .2%} 
                  доля возвратов {name_2}: {concert_users: .2%}
                  больше у: {compare}
                ''')
        print()
    
    # вызов compare_type(
    #     col='first_event_type',
    #     name_1='спорт',
    #     name_2='концерты',
    #     binary_col='is_two'
    # )

    # Гипотеза 2
    # Сравнение регионов с построением столбчатой диаграммы и линии доли 
    # По умолчанию linecolor='red', linewidth=2, marker='o'
    
    def compare_region(
            self,
            col,
            binary_col,
            agg_func,
            sort_col,
            linecolor='red',
            linewidth=2,
            marker='o',
    ):

        region_compare = self.user_profile.groupby(
            col)[binary_col].agg(agg_func)
        if 'mean' in agg_func:
            region_compare['mean'] = region_compare['mean'] * 100
            print(f'\n{agg_func} по {col}:')
            print(region_compare.sort_values(by=sort_col, ascending=False))
        else:
            print(f'\n{agg_func} по {col}:')
            print(region_compare.sort_values(by=sort_col, ascending=False))

        # Подготовим данные для графика
      
        region_compare = region_compare.sort_values(
            by=sort_col, ascending=False).head(20)

        # Задаем сетку для графика
      
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # CТроим первый график - столбчатую диаграмму
      
        ax1.bar(
            data=region_compare,
            x=region_compare.index,
            height=region_compare[agg_func[0]]
        )
      
        # Настраиваем график
      
        ax1.set_xlabel(col)
        ax1.set_ylabel('Количество')
        ax1.grid(axis='y')
      
        # Уберем ошибку Fixed Locator
      
        ax1.set_xticks(range(len(region_compare.index)))
        ax1.set_xticklabels(region_compare.index, rotation=45,
                            ha='right')  # настриваем подписи оси x

        # Создадим вторую ось для долей
      
        ax2 = ax1.twinx()

        # Строим линию долей возврата по регионам
      
        ax2.plot(
            region_compare.index,
            region_compare[agg_func[1]],
            color=linecolor,
            linewidth=linewidth,
            marker=marker,
            label='Доля'
        )

        # Настраиваем подписи и ось для второго графика
      
        ax2.set_ylabel('Доля', color=linecolor)
        ax2.tick_params(axis='y', labelcolor=linecolor)

        plt.legend()
        plt.title(f'Сравнение {col} и {agg_func[1]}')
        plt.tight_layout()
        plt.show()
    
    # вызов compare_region(
    #     col='first_region',
    #     binary_col='is_two',
    #     agg_func=['count', 'mean'],
    #     sort_col='count'
    # ) 

    # Метод для расчета и построения гистограмм для 
    # распределения непрерывных значений по бинарному признаку
    
    def return_revenue(self, col, group_col, agg_list):

        # Построим графики плотности распределения для обоих групп
        
        plt.figure(figsize=(12, 6))

        ax = sns.histplot(
            data=self.user_profile,
            x=col,
            hue=group_col,
            bins=50,
            alpha=0.5,
            stat='density',
            common_norm=False,
            edgecolor='black',
        )

        ax.get_legend().set_title('Количесиво заказов')
        ax.get_legend().get_texts()[0].set_text('0 - Менее 2')
        ax.get_legend().get_texts()[1].set_text('1 - 2 и более')
        plt.title('Распеределение средней выручки')
        plt.xlabel('Средняя выручка (руб.)')
        plt.ylabel('Плотность')
        plt.xlim(left=0)
        plt.tight_layout()
        plt.show()

        # Посчитаем стат данные для обоих групп
        
        self.user_profile.groupby(group_col)[col].agg(agg_list).round(2)
    
    # вызов return_revenue(
    #     col='avg_revenue',
    #     group_col='is_two',
    #     agg_list=['sum', 'min', 'max', 'mean', 'median']
    # )

    # Метод для распределения данных по дням недели с 
    # построением столбчатой диаграммы с линией доли бинарного признака

    def time_char(self, new_col, date_col, binary_col, agg_list, sort_col):

        self.user_profile[new_col] = self.user_profile[date_col].dt.day_name()

        # вызов готового для этого случая метода для построения 
        # столбчатой диаграммы с линией доли бинарного признака 

        self.compare_region(
            col=new_col,
            binary_col=binary_col,
            agg_func=agg_list,
            sort_col=sort_col
        )

    # вызов time_char(
    #     new_col='week_day',
    #     date_col='first_order',
    #     binary_col='is_two',
    #     agg_list=['count', 'mean'],
    #     sort_col='count'
    # )

    # Метод для подсчета корреляций с выводом тепловой карты 
    # и графика распределения scatterplot для проверки корреляции
    
    def corr(self, interval_cols, col, cols_for_scat_plot):
        correlation_matrix = self.user_profile.phik_matrix(
            interval_cols=interval_cols)

        print(f'\nКорреляционная матрица с коэффициентом phi_k для {col}:')
        print(
            correlation_matrix.loc[
                correlation_matrix.index != col
            ][[col]].sort_values(
                by=col, ascending=False
            )
        )

        # Визуализируем полученные данные
        # Строим тепловую карту
        
        plt.figure(figsize=(2, 6))

        data_heatmap = (correlation_matrix.loc[correlation_matrix.index != col]
                        [[col]].sort_values(by=col, ascending=False)
                        )
        sns.heatmap(data_heatmap,
                    annot=True,
                    fmt='.2f',
                    cmap='coolwarm',
                    linewidth=0.5
                    )
        
        # Настраиваем подписи
        
        plt.title('Тепловая карта коэффициента phi_k \n для {col}')
        plt.xlabel(col)

        # выводим тепловую карту
        
        plt.show()

        # Проверка корреляции, построение scatterplot

        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        for ax, (name, values) in zip(axes, self.user_profile[cols_for_scat_plot].items()):
            sns.scatterplot(
                data=self.user_profile,
                x=self.user_profile[name],
                y=self.user_profile[col],
                alpha=0.5,
                legend=True,
                ax=ax
            )
            ax.set_title(f'зависимость {col} от {name}')
            ax.set_xlabel(name)
            ax.set_ylabel(col)
            ax.grid(True, alpha=0.5, linestyle='--')

            plt.suptitle(f'зависимость {col}')
            plt.tight_layout()
            plt.show
    
    # вызов corr(
    #     interval_cols=['total_orders', 'avg_revenue',
    #                    'avg_time_between_orders'],
    #     col='total_orders',
    #     cols_for_scat_plot=['first_order', 'last_order']
    # )

    # Проверка сезонности по исходным данным
    # с построением столбчатой диаграммы
    
    def season_check(self, col):
        monthly_orders = self.df.groupby(self.df[col].dt.month_name())[
            col].count().sort_values(ascending=False)
        print('\nКоличество заказов по месяцам:')
        print(monthly_orders)

        plt.figure(figsize=(12, 6))

        monthly_orders.plot(
            kind='bar',
            edgecolor='black',
            rot=45
        )
        plt.title('Количество заказов по месяцам')
        plt.xlabel('Месяц')
        plt.ylabel('Количество заказов')
        plt.tight_layout()
        plt.show()

    # вызов season_check(col='order_dt')
