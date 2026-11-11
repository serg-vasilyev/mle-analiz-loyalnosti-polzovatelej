from src.processing import DataProcessor
import subprocess
import sys


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

    # Удаление лишних столбцов
    process.del_cols(del_cols=['data', 'nominal', 'curs', 'cdx' ])
    # Проверка пропусков
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
        cols_top_tail=['user_id', 'event_name',
                       'service_name', 'region_name', 'city_name']
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

# ИССЛЕДОВАТЕЛЬСКИЙ АНАЛИХ ДАННЫХ

    # Распределение пользователей по признакам
    process.users_by_cat(
        cols=['first_event_type', 'first_device', 'first_region']
    )

    # ber_plots
    process.user_cat_bar_plot(
        cols=['first_event_type', 'first_device', 'first_region']
    )  # По умолчанию edgecolor='black'

    # Анализ возврата с построением bar plots и линии общей средней
    process.return_analysis(
        binary_col='is_two',
        cat_cols=['first_event_type', 'first_device', 'first_region'],
        cnt_col='first_region'
    )  # linecolor='magenta',linestyle='--',linewidth=2

    # Проверка продуктовых гипотез
    # Гипотеза 1
    process.compare_type(
        col='first_event_type',
        name_1='спорт',
        name_2='концерты',
        binary_col='is_two'
    )
    # Гипотеза 2
    process.compare_region(
        col='first_region',
        binary_col='is_two',
        agg_func=['count', 'mean'],
        sort_col='count'
    )  # linecolor='red', linewidth=2, marker='o'

    # Выручка и состав заказа

    process.return_revenue(
        col='avg_revenue',
        group_col='is_two',
        agg_list=['sum', 'min', 'max', 'mean', 'median']
    )

    # Временные характеристики

    process.time_char(
        new_col='week_day',
        date_col='first_order',
        binary_col='is_two',
        agg_list=['count', 'mean'],
        sort_col='count'
    )

    # Корреляция

    process.corr(
        interval_cols=['total_orders', 'avg_revenue',
                       'avg_time_between_orders'],
        col='total_orders',
        cols_for_scat_plot=['first_order', 'last_order']
    )

    # Проверка сезонности
    process.season_check(col='order_dt')

    if sys.platform == 'win32':
        subprocess.run('', shell=True)

    print('''
    \033[1;33mОбщие выводы\033[0m

 - \033[1;33mПортрет и поведение пользователя:\033[0m
   
   Подавляющее большиство заказов \033[1;33m(~82,9%)\033[0m совершаются с \033[1;33mмобильных устройств\033[0m. 
   Это делает мобильное приложение или адаптивную веб версию ключевым "траффиком". 
   \033[1;33m(~75%)\033[0m повторных покупок совершается в течении одного дня. Обычный размер заказа составляет \033[1;33m2-3 билета\033[0m.
 
 - \033[1;33mТочки входа и лидеры категорий:\033[0m
   
   Главным типом мероприятия для привлечения клиентов выступают \033[1;33mконцерты (~44.7% первых заказов)\033[0m 
   и \033[1;33mтеатры (19.8%)\033[0m. Лидером среди регионов является \033[1;33mКаменевский регион\033[0m, 
   среди городов - \033[1;33mГлиногорск\033[0m
 
 - \033[1;33mУдержание и выручка:\033[0m
   
   Общая доля пользователей, совершивших 2 и более заказа, составляет около \033[1;33m61.07%\033[0m. 
   Лояльные клиенты генерируют более стабильную и высокую медианную выручку 
   (медиана \033[1;33m503.16 руб\033[0m. против \033[1;33m388.81 руб.\033[0m у новичков)
 
 - \033[1;33mВлияние дней недели:\033[0m
   
   Наибольшая вероятность возврата за повторной покупкой приходится на \033[1;33mсубботу и понедельник (около 62.5%)\033[0m. 
 
 - \033[1;33mОпровержение гипотез:\033[0m
   
   Продуктовые гипотезы \033[1;33mне подтвердились\033[0m. Возвратов больше у тех кто первый раз оформил заказ на концерты. 
   Доля возвратов с увеличением активности увеличивается - \033[1;33mне подтверждается)\033[0m

    \033[1;33mРекомендации\033[0m

 - Поскольку  подавляющее большиство заказов \033[1;33m(~82,9%)\033[0m совершаются с \033[1;33mмобильных устройств\033[0m. 
   Можно направить усилия на модернизацию или увеличение функционала и удобство мобильного приложения 
   или адаптивного под мобильные устройства веб-сервиса

 - Так как большинство покупок совершается в течение одного дня можно наладить push рассылки сразу 
   или через несколько часов после сделанного заказа

 - Сделать упор в рекламных кампаниях на концерты и спектакли в театрах

 - Увеличить интенсивность рекламных рассылок в пятницу вечером, субботу и понедельник, 
   это дни когда люди склонны возвращаться.
''')
    
# вызов функции:
if __name__ == "__main__":
    main()
