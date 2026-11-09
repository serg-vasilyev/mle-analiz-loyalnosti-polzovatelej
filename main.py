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
    process.tenge_conv_proc(new_col='revenue_rub',
                            revenue_col='revenue',
                            nominal='nominal',
                            rate='curs',
                            currency_code='currency_code',
                            code='kzt')

    # Проверка провусков
    process.nulls()

    # Оптимизация размерности числовых столбцов
    process.optimization(cols_int=['order_id', 'tickets_count', 'event_id'],
                         cols_float=['days_since_prev'])

    # Проверка дубликатов
    # keep = 'first' по умолчанию
    process.duplicates_check(cols=["order_id", "service_name"])

    # Приведение к нижнему регистру столбцов со строками
    process.lower_register(cols=['service_name', 'region_name', 'city_name'])

    # Проверка неявных дубликатов
    process.duplicates_check(cols=["order_id", "service_name"])

    # Проверка неявных дубликатов в связке с user_id
    process.duplicates_check(cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
                             keep=False)

    # Вывод на экран неявных дублткатов
    process.show_duplicates(cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
                            keep=False, sort_cols='user_id')  # sort_cols=None, ascending=True по умолчанию

    # Удаление дубликатов
    process.delete_duplicates(cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
                              sort_cols='days_since_prev',
                              ascending=False)  # sort_cols=None, ascending=True, keep='first' по умолчанию

    # Проверка корректности удаления дубликатов
    process.duplicates_check(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"])

    # Вывод информации по столбцам object
    process.obj_info(cols=['device_type_canonical', 'event_type_main'],
                     cols_top_tail=['user_id', 'event_name', 'service_name', 'region_name', 'city_name'])

    # Вывод инфо по числовым столбцам с гистограммами и боксплотами
    process.fig_info(cols=['tickets_count', 'days_since_prev', 'revenue_rub'],
                     rows=6, 
                     graph_cols=1)  # edgecolor='white', color='skyblue'

    # Фильтрация по 99му процентилю
    process.filtration(cols='revenue_rub', quant=0.99)

    # вывод гистограммы и boxplot для выручки после фильтрации
    process.fig_info(cols='revenue_rub',
                     rows=1, 
                     graph_cols=2)  # edgecolor='white', color='skyblue'

    # Вывод столбчатой диаграммы для tickets_count
    process.bar_plot(col='tickets_count')  # edgecolor='white', color='skyblue'

    # Подсчеты отрицательной выручки
    process.neg_revenue_info(col='revenue_rub')

    # Фильтрация отрицательной выручки
    process.neg_revenue_filt(col='revenue_rub')

    # Вывод информации о количестве строк после предобработки
    process.cnt_df_after_filt()

    # вывод гистограммы после фильтрации по отрицательным числам
    process.fig_info(cols='revenue_rub', rows=1, graph_cols=2)  # edgecolor='white', color='skyblue


# вызов функции:
if __name__ == "__main__":
    main()
