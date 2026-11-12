from src.processing import DataProcessor
import subprocess
import sys


def main():
    process = DataProcessor()

# Загрузка данных из БД
# по умолчанию folder_name='data'
    
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
                    )

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
    # по умолчанию cols_int=None, cols_float=None
    
    process.optimization(
        cols_int=['order_id', 'tickets_count', 'event_id'],
        cols_float=['days_since_prev']
    )

    # Проверка дубликатов
    # по умолчанию keep='first' - первое вхождение не дубликат
    
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
    # по умолчанию keep='first', sort_cols=None, ascending=True
    
    process.show_duplicates(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
        keep=False, sort_cols='user_id'
    )  

    # Удаление дубликатов
    # По умолчанию sort_cols=None, ascending=True, keep='first'
    
    process.delete_duplicates(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"],
        sort_cols='days_since_prev',
        ascending=False
    )  

    # Проверка корректности удаления дубликатов
    
    process.duplicates_check(
        cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"]
    )

    # Вывод информации по столбцам object
    # по умолчанию cols=None, cols_top_tail=None

    # !!! Записываем нужные значения для финального отчета в переменные !!!
    
    process.obj_info(
        cols=['device_type_canonical', 'event_type_main'],
        cols_top_tail=['user_id', 'event_name',
                       'service_name', 'region_name', 'city_name']
    )

    top_cnt = process.obj_info(
        cols=['device_type_canonical', 'event_type_main'],
        cols_top_tail=['user_id', 'event_name',
                       'service_name', 'region_name', 'city_name']
                       )

    top_city_name = top_cnt['city_name'].index[0]

    # Вывод инфо по числовым столбцам с гистограммами и боксплотами
    # edgecolor='white', color='skyblue' по умолчанию для графиков
    
    process.fig_info(cols=['tickets_count', 'days_since_prev', 'revenue_rub'])

    # Фильтрация по 99му процентилю
    
    process.filtration(cols='revenue_rub', quant=0.99)

    # вывод гистограммы и boxplot для выручки после фильтрации
     # По умолчанию edgecolor='white', color='skyblue' для графиков
    
    process.fig_info(cols='revenue_rub')  

    # Вывод столбчатой диаграммы для tickets_count
     # По умолчанию edgecolor='white', color='skyblue' для графиков
    
    process.bar_plot(col='tickets_count')  

    # Подсчеты отрицательной выручки
    
    process.neg_revenue_info(col='revenue_rub')

    # Фильтрация отрицательной выручки
    
    process.neg_revenue_filt(col='revenue_rub')

    # Вывод информации о количестве строк после предобработки
    
    process.cnt_df_after_filt()

    # вывод гистограммы после фильтрации по отрицательным числам и 
    # формирование данных для отчета

    # !!! Записываем нужные значения для финального отчета в переменные !!!
    
    days_quant, median_dict = process.fig_info(
        cols=['tickets_count', 'days_since_prev', 'revenue_rub'],
        plot_col='revenue_rub'
        ) 
    days_quant_75 = days_quant['days_since_prev']
    tickets_median = median_dict['tickets_count'] 

    days_recommendation = (
        'Так как большинство покупок совершается в течение одного дня,\n'
        '   можно наладить push рассылки сразу или через несколько часов\n' 
        '   после сделанного заказа' 
        if days_quant_75 <= 1 
        else 'Настроить персонализированные предложения и скидки'
        ) 

    # Создание профиля пользователя
    # По умолчанию binary_col_name=None на случай, если бинарный столбец не нужен
    
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
    # По умолчанию edgecolor='white', color='skyblue'
    
    process.analytic_hist_box_plot(
        cols=['total_orders', 'avg_time_between_orders']
    )

    # Проверяем 99 и 95 процентиль
    # По умолчанию cols=None, quants=None
    
    process.analytic_before_filt_check(
        cols=['total_orders', 'avg_time_between_orders'],
        quants=[0.99, 0.95]
    )  

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
    
    # !!! Записываем нужные значения для финального отчета в переменные !!!

    cat_stats =  process.users_by_cat(
        cols=['first_event_type', 'first_device', 'first_region']
        )
    
    top_device_name = cat_stats['first_device'].index[0]
    top_device_share = cat_stats['first_device'].iloc[0]
    top_event_name = cat_stats['first_event_type'].index[0]
    top_event_share = cat_stats['first_event_type'].iloc[0]
    second_event_name = cat_stats['first_event_type'].index[2]
    second_event_share = cat_stats['first_event_type'].iloc[2]
    top_region_name = cat_stats['first_region'].index[0]
    top_region_share = cat_stats['first_region'].iloc[0]

    device_report = ( 'Мобильное приложение и адаптивную вэб-версию' 
                     if top_device_share > cat_stats['first_device'].iloc[1] 
                     else 'ПК версию сайта'
                     )

    device_recommendation = (
        'Можно направить усилия на модернизацию или увеличение функционала\n'
        '   и удобство мобильного приложения или адаптивного под мобильные устройства веб-сервиса' 
        if top_device_share > cat_stats['first_device'].iloc[1] 
        else 'Можно направить усилия на модернизацию или увеличение\n' 
        'функционала и удобство ПК версии сайта'
        )

    # ber_plots
     # По умолчанию edgecolor='black'
    
    process.user_cat_bar_plot(
        cols=['first_event_type', 'first_device', 'first_region']
    )  

    # Анализ возврата с построением bar plots и линии общей средней
    # По умолчанию edgecolor='black', linecolor='magenta', linestyle='--',linewidth=2

    # !!! Записываем нужные значения для финального отчета в переменные !!!
    
    user_share = process.return_analysis(
        binary_col='is_two',
        cat_cols=['first_event_type', 'first_device', 'first_region'],
        cnt_col='first_region'
    )  

    # Проверка продуктовых гипотез
    # Гипотеза 1
    
    # !!! Записываем нужные значения для финального отчета в переменные !!!
    
    event_type = process.compare_type(
        col='first_event_type',
        name_1='спорт',
        name_2='концерты',
        binary_col='is_two'
    )

    event_type_report = 'подтверждается' if event_type == 'спорт' else 'не подтверждается'
    
    # Гипотеза 2
    # По умолчанию linecolor='red', linewidth=2, marker='o'
    
    # !!! Записываем нужные значения для финального отчета в переменные !!!
    
    region_agg = process.compare_region(
        col='first_region',
        binary_col='is_two',
        agg_func=['count', 'mean'],
        sort_col='count'
    )  

    top_region_mean = region_agg['mean'].iloc[0]
    other_regions = region_agg.iloc[1:]

    region_report = (
        'Подтверждается' 
        if (top_region_mean > other_regions['mean']).all() 
        else 'не подтверждается'
        )   

    # Выручка и состав заказа
    
    # !!! Записываем нужные значения для финального отчета в переменные !!!

    return_stat = process.return_revenue(
        col='avg_revenue',
        group_col='is_two',
        agg_list=['sum', 'min', 'max', 'mean', 'median']
    )

    median_0 = return_stat.loc[0, 'median']
    median_1 = return_stat.loc[1, 'median']
    
    return_report = 'более' if median_1 > median_0 else 'менее' if median_0 > median_1 else 'такую же'

    # Временные характеристики
    
    # !!! Записываем нужные значения для финального отчета в переменные !!!

    day_agg = process.time_char(
        new_col='week_day',
        date_col='first_order',
        binary_col='is_two',
        agg_list=['count', 'mean'],
        sort_col='count'
    )

    day_agg_sorted = day_agg.sort_values(by = 'mean', ascending = False)
    best_day = day_agg_sorted.index[0]
    best_day_mean = day_agg_sorted['mean'].iloc[0]
    second_day = day_agg_sorted. index[1]
    second_day_mean = day_agg_sorted['mean'].iloc[1]

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

    print(f'''
    \033[1;33mОбщие выводы\033[0m

 - \033[1;33mПортрет и поведение пользователя:\033[0m
   
   Подавляющее большиство первых заказов \033[1;33m~{top_device_share:}%\033[0m совершались 
   с \033[1;33m{top_device_name}\033[0m. 
   Это делает {device_report} ключевым "траффиком". 
   
   \033[1;33m~75% (по 75му процентилю)\033[0m повторных покупок совершается 
   в течении \033[1;33m{days_quant_75} дня / дней \033[0m. 
   Обычный размер заказа составляет \033[1;33m{tickets_median} билета\033[0m.
 
 - \033[1;33mТочки входа и лидеры категорий:\033[0m
   
   Главным типом мероприятия для привлечения клиентов выступают 
   \033[1;33m{top_event_name} (~{top_event_share:}% первых заказов)\033[0m 
   и \033[1;33m{second_event_name} (~{second_event_share})%\033[0m. 
   Лидером среди регионов является \033[1;33m{top_region_name}\033[0m, 
   среди городов - \033[1;33m{top_city_name}\033[0m
 
 - \033[1;33mУдержание и выручка:\033[0m
   
   Общая доля пользователей, совершивших 2 и более заказа, 
   составляет около \033[1;33m{user_share}%\033[0m. 
   Лояльные клиенты генерируют {return_report} высокую медианную выручку 
   (медиана \033[1;33m{median_1} руб\033[0m. 
   против \033[1;33m{median_0} руб.\033[0m у новичков)
 
 - \033[1;33mВлияние дней недели:\033[0m
   
   Наибольшая вероятность возврата за повторной покупкой 
   приходится на \033[1;33m{best_day} (~{best_day_mean:.2f}%) 
   и {second_day} (~{second_day_mean:.2f}%\033[0m. 
 
 - \033[1;33mРезультаты проверки гипотез:\033[0m
   
   Продуктовые гипотезы: 
   
   Гипотеза 1 - \033[1;33m{event_type_report}\033[0m. 
   Возвратов больше у тех кто первый раз оформил заказ на \033[1;33m{event_type}\033[0m. 
   
   Гипотеза 2 - Доля возвратов с увеличением активности увеличивается - 
   \033[1;33m{region_report}\033[0m

    \033[1;33mРекомендации\033[0m

 - Поскольку  подавляющее большиство заказов \033[1;33m{top_device_share:}%\033[0m 
   совершаются с \033[1;33m{top_device_name}\033[0m. 
   {device_recommendation}

 - {days_recommendation}

 - Сделать упор в рекламных кампаниях на \033[1;33m{top_event_name}\033[0m и 
   \033[1;33m{second_event_name}\033[0m

 - Увеличить интенсивность рекламных рассылок в \033[1;33m{best_day}\033[0m и 
   \033[1;33m{second_day}\033[0m, это дни когда люди склонны возвращаться.
'''
)
    
# вызов функции:
if __name__ == "__main__":
    main()
