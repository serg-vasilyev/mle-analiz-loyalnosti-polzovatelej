from src.processing import DataProcessor


def main():
    process = DataProcessor()

# Загрузка данных из БД
    process.load_db(query=''' SELECT
                            p.user_id,
                            p.device_type_canonical,
                            p.order_id,
                            p.created_dt_msk AS order_dt,
                            p.created_ts_msk AS order_ts,
                            p.currency_code,
                            p.revenue,
                            p.tickets_count,
                            p.created_dt_msk::date - LAG(p.created_dt_msk::date) OVER (
                                PARTITION BY p.user_id 
                                ORDER BY p.created_dt_msk
                                ) AS days_since_prev,
                            e.event_id,
                            e.event_name_code AS event_name,
                            e.event_type_main,
                            p.service_name,
                            r.region_name,
                            c.city_name
                        FROM afisha.purchases as p
                        LEFT JOIN afisha.events as e 
                            ON p.event_id = e.event_id 
                        LEFT JOIN afisha.city as c 
                            ON e.city_id = c.city_id
                        LEFT JOIN afisha.regions as r 
                            ON c.region_id = r.region_id
                        WHERE p.device_type_canonical IN ('mobile', 'desktop')
                            AND e.event_type_main != 'фильм'
                        ORDER BY p.user_id
                        ''',
                    csv_name='afisha_db.csv'
                    )  # folder_name = 'data' по умолчанию

    # Загрузка данных о курсе тенге
    # folder_name='data' по умолчанию
    process.load_tenge_csv(file_name='final_tickets_tenge_df.csv')

    # Посмотрим на содержимое датасета
    process.check_data()

    # Соединяем датафреймы
    # tenge_date = 'data' по умолчанию
    process.tenge_conv_merge(period_col='order_dt')

    # конвертируем тенге в рубли с созданием нового столбца
    process.tenge_conv_proc(
        new_col='revenue_rub',
        revenue_col='revenue',
        nominal='nominal',
        rate='curs',
        currency_code='currency_code',
        code='kzt'
        )

    # Проверка провусков
    process.nulls()

    # Оптимизация размерности числовых столбцов
    process.optimization(
        cols_int=['order_id', 'tickets_count', 'event_id'],
        cols_float=['days_since_prev']
        )

    # Проверка дубликатов
    # keep = 'first' по умолчанию
    process.duplicates_check(cols=["order_id", "service_name"])

    # Приведение к нижнему регистру столбцов со строками
    process.lower_register(cols=['service_name', 'region_name', 'city_name'])

    # Проверка неявных дубликатов
    process.duplicates_check(cols=["order_id", "service_name"])

    # Проверка неявных дубликатов в связке с user_id
    process.duplicates_check(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
        keep=False
        )

    # Вывод на экран неявных дублткатов
    process.show_duplicates(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
        keep=False, sort_cols='user_id'
        )  # sort_cols=None, ascending=True по умолчанию

    # Удаление дубликатов
    process.delete_duplicates(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
        sort_cols='days_since_prev',
        ascending=False
        )  # sort_cols=None, ascending=True, keep='first' по умолчанию

    # Проверка корректности удаления дубликатов
    process.duplicates_check(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"]
        )

    # Вывод информации по столбцам object
    process.obj_info(
        cols=['device_type_canonical', 'event_type_main'],
        cols_top_tail=['user_id', 'event_name', 'service_name', 'region_name', 'city_name']
        )

    # Вывод инфо по числовым столбцам с гистограммами и боксплотами
    # edgecolor='white', color='skyblue'
    process.fig_info(cols=['tickets_count', 'days_since_prev', 'revenue_rub'])

    # Фильтрация по 99му процентилю
    process.filtration(cols='revenue_rub', quant=0.99)

    # вывод гистограммы и boxplot для выручки после фильтрации
    process.fig_info(cols='revenue_rub')  # edgecolor='white', color='skyblue'

    # Вывод столбчатой диаграммы для tickets_count
    process.bar_plot(col='tickets_count')  # edgecolor='white', color='skyblue'

    # Подсчеты отрицательной выручки
    process.neg_revenue_info(col='revenue_rub')

    # Фильтрация отрицательной выручки
    process.neg_revenue_filt(col='revenue_rub')

    # Вывод информации о количестве строк после предобработки
    process.cnt_df_after_filt()

    # вывод гистограммы после фильтрации по отрицательным числам
    process.fig_info(cols='revenue_rub')  # edgecolor='white', color='skyblue

    # Создание профиля пользователя
    process.user_profile_create(
        sort_cols='order_ts',
        group_cols='user_id',
        binary_col_name='is_two',
        col_for_binary='total_orders',
        first_order=('order_dt', 'min'),
        last_order=('order_dt', 'max'),
        first_device=('device_type_canonical', 'first'),
        first_region=('region_name', 'first'),
        first_event_type=('event_type_main', 'first'),
        total_orders=('order_id', 'count'),
        avg_revenue=('revenue_rub', 'mean'),
        avg_time_between_orders=('days_since_prev', 'mean')
    )

    # Поиск аномалий
    process.anomaly_check(
        mean_col='avg_revenue',
        binary_col='is_two',
        info_cols=['total_orders', 'avg_time_between_orders']
    )

    # строим гистограмму и boxplot для total_orders, avg_time_between_orders
    # edgecolor = 'white', color = 'skyblue'
    process.analytic_hist_box_plot(
        cols=['total_orders', 'avg_time_between_orders']
        )

    # Проверяем 99 и 95 процентиль
    process.analytic_before_filt_check(
        cols=['total_orders', 'avg_time_between_orders'],
        quants=[0.99, 0.95]
        )  # по умолчанию столбцы и квантили None

    # Фильтрация
    process.analytic_filt(
        cols=['total_orders', 'avg_time_between_orders'], quant=0.99
        )

    # строим гистограмму и boxplot для total_orders, avg_time_between_orders после фильтрации
    # edgecolor = 'white', color = 'skyblue'
    process.analytic_hist_box_plot(
        cols=['total_orders', 'avg_time_between_orders']
        )


# вызов функции:
if __name__ == "__main__":
    main()
