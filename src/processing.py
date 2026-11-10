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

        # load_db(query ='...', csv_name = 'afisha_db.csv') folder_name = 'data' по умолчанию

        # Загрузка файла с курсами валют тенге
    def load_tenge_csv(self, file_name, folder_name='data'):
        self.tenge_rate_df = pd.read_csv(
            f'{self.project_root}/{folder_name}/{file_name}'
            )

    # load_tenge_csv(file_name='final_tickets_tenge_df.csv') folder_name='data' по умолчанию

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

        # check_data()

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

    # -> tenge_conv_merge(period_col = 'order_dt') tenge_date = 'data' по умолчанию

    def tenge_conv_proc(
            self, 
            new_col, 
            revenue_col, 
            nominal, rate, 
            currency_code, 
            code
            ):
        
        # Создаем столбец с рублями
        self.df[new_col] = np.where(
            self.df[currency_code] == code,
            (self.df[revenue_col] / self.df[nominal]) * self.df[rate],
            self.df[revenue_col]
        )

        print('\nвесь датасет после конвериации:')
        print(self.df[[currency_code, revenue_col, new_col]])
        print('\nвалюта kzt:')
        print(
            self.df[[currency_code, revenue_col, self.period_col,
            rate, new_col]].loc[self.df[currency_code] == code]
            )

        # Удаление столбцов
        self.df = self.df.drop(columns=[self.tenge_date, nominal, rate, 'cdx'])

        print('\nПроверка после удаления:')
        print(self.df.info())

    # Поиск пропусков
    def nulls(self):

        # подсчет пропусков
        print('\nКоличество пропусков')
        print(self.df.isna().sum())

        print('\nпропуски в процентах:')
        print((self.df.isna().sum() / self.df.shape[0] * 100).round(2))

        # nulls()

    def optimization(self, cols_int, cols_float):
        
        # оптимизируем столбцы с целочисленными значениями
        for col in cols_int:
            self.df[col] = pd.to_numeric(self.df[col], downcast='integer')

        # оптимизируем столбец 'days_since_prev'
        for col in cols_float:
            self.df[col] = pd.to_numeric(self.df[col], downcast='float')

        print('\nПроверка оптимизации:')
        print(self.df.info())

        # optimization(cols_int = ['order_id', 'tickets_count', 'event_id'], cols_float = ['days_since_prev'] )

    def duplicates_check(self, cols, keep='first'):

        # проверим на дубликаты датафрейм
        print(f'\nДубликаты в датафрейме: {self.df.duplicated().sum()}')

        # проверим столбец order_id на дубликаты
        print(
            f'\nЯвные/неявные дубликаты в столбце/столбцах {cols}: {self.df.duplicated(subset=cols, keep=keep).sum()}'
            )

        # duplicates_check (cols=["order_id", "service_name"])

    def lower_register(self, cols):

        # приведем к нижнему регистру 'service_name', 'region_name', 'city_name'
        for col in cols:
            self.df[col] = self.df[col].str.lower()

        print(f'\nпосле нормализации:')

        # lower_register(cols=['service_name', 'region_name', 'city_name'])

    def show_duplicates(
            self, 
            cols, 
            keep='first', 
            sort_cols=None, 
            ascending=True
            ):
        
        # Выведем эти строки
        print('\nЯвные/неявные дубликаты в столбце/столбцах {cols}:')
        pd.set_option('display.max_rows', None)
        duplicated_df = self.df[self.df.duplicated(
            subset=cols,
            keep=keep)
        ]

        if sort_cols is not None:
            duplicated_df.sort_values(sort_cols, ascending=ascending)
        print(duplicated_df)
        return duplicated_df

    def delete_duplicates(
            self, 
            cols, 
            sort_cols=None, 
            ascending=True, 
            keep='first'):
        
        # Зафиксируем начальное количество строк
        self.rows_before = self.df.shape[0]

        # Удаляем дубликаты
        self.df = (
            self.df.sort_values(by='days_since_prev', ascending=False)
            .drop_duplicates(
                subset=["user_id", "order_ts", "revenue",
                        "event_id", "tickets_count"],
                keep='first'
            ).sort_index()
        )

        df_processed = self.df

        if sort_cols is not None:
            df_processed = df_processed.sort_values(
                by=sort_cols, ascending=ascending)
        
        df_processed = df_processed.drop_duplicates(
            subset=cols,
            keep=keep
        )

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

    def fig_info(self, cols, edgecolor='white', color='skyblue'):

        if isinstance(cols, str):
            cols = [cols]

        # Теперь посмотрим на числовые значения и проверим выбросы, с построением гистограмм и боксплотов
        print('\nИнформация по числовым столбцам:')
        print(self.df.describe())

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

    def filtration(self, cols, quant):

        # Зафиксируем количество строк до фильтрации
        len_before_filt = self.df.shape[0]

        # Отфильтруем столбец revenue_rub по 99 процентилю
        quantile_quant = self.df[cols].quantile(quant)
        self.df = self.df.loc[self.df[cols] <= quantile_quant]

        print(
            f'\nОтфильтровано по {quant} квантилю: {len_before_filt - self.df.shape[0]}')
        print(
            f'\nв процентах: {((len_before_filt - self.df.shape[0]) / len_before_filt):.2%}')

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

    def neg_revenue_info(self, col):

        # разберемся с отрицательной выручкой
        print(
            f'\nКоличество отрицательной и нулевой выручки: {self.df.loc[self.df[col] <= 0].shape[0]}'
            )
        print(
            f'\nв процентах: {((self.df.loc[self.df[col] <= 0].shape[0]) / self.df.shape[0]):.4%}'
            )

    def neg_revenue_filt(self, col):
        self.df = self.df.loc[self.df[col] > 0]
        print(
            f'\nколичество удаленных строк включая дубликаты: {self.rows_before - self.df.shape[0]}'
            )
        print(
            f'\nколичество удаленных строк в процентах: {((self.rows_before - self.df.shape[0]) / self.rows_before):.4%}'
            )

    def cnt_df_after_filt(self):
        print(
            f'\nКоличество строк в предобработанном датафрейме: {self.df.shape[0]}'
            )


# СОЗДАНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ


    def user_profile_create(
            self,
            sort_cols,
            group_cols,
            binary_col_name,
            col_for_binary,
            **kwargs
    ):

        # Сортируем датафрейм
        df_sorted = self.df.sort_values(sort_cols)

        # Создаем профиль
        self.user_profile = df_sorted.groupby(group_cols).agg(
            **{name: (col, op) for name, (col, op) in kwargs.items()}
        )

        # Добавляем бинарный столбец для пользователей сделавших более 2х заказов
        self.user_profile[binary_col_name] = (
            self.user_profile[col_for_binary] >= 2
            ).astype(int)

        print('\nПрофиль пользователя:')
        print(self.user_profile.head(10))

    # Поиск аномалий
    def anomaly_check(self, mean_col, binary_col, info_cols, edgecolor='white', color='skyblue'):

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

    # Построим гиcтограммы и боксплоты для статистических данных

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

    # Проверка количества строк для удаления по столбцам и квантилям на выбор пользователя
    def analytic_before_filt_check(self, cols=None, quants=None):
        cols = cols or []
        quants = quants or []

        if not cols or not quants:
            print('Не указаны столбцы или квантили для расчета')

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
                    f'количество строк более {q_val} для {col_name}: {del_count}'
                    )

                del_share = del_count / self.user_before
                print(
                    f'Доля строк по {col_name} для удаления: {del_share: .2%}'
                    )
                print()

    # Фильтрация
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
            f'количество отфильтрованных строк: {self.user_before - self.user_profile.shape[0]}'
            )
        print(
            f'Доля отфильтрованных строк: {((self.user_before - self.user_profile.shape[0]) / self.user_before): .2%}'
            )
        print()

        # изменение после фильтрации
        print('изменения после филбтрации:')
        print(self.user_profile.describe())
        print()
