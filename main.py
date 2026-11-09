# Загрузка данных из БД
# load_db(query ='...', csv_name = 'afisha_db.csv') folder_name = 'data' по умолчанию

# Загрузка данных о курсе тенге
# load_tenge_csv(file_name='final_tickets_tenge_df.csv') folder_name='data' по умолчанию

 
# Посмотрим на содержимое датасета
# check_data()

# -> tenge_conv_merge(period_col = 'order_dt') tenge_date = 'data' по умолчанию

# конвертируем тенге в рубли с созданием нового столбца
# tenge_conv_proc(new_col='revenue_rub, revenue_col='revenue', nominal='nominal', rate='curs', currency_code='currency_code'. code='kzt

# Проверка провусков
# nulls()

# Оптимизация размерности числовых столбцов
# optimization(cols_int = ['order_id', 'tickets_count', 'event_id'], cols_float = ['days_since_prev'] )

# Проверка дубликатов
# duplicates_check (cols=["order_id", "service_name"]) keep = 'first' по умолчанию

# Приведение к нижнему регистру столбцов со строками
# lower_register(cols=['service_name', 'region_name', 'city_name'])

# Проверка неявных дубликатов
# duplicates_check (cols=["order_id", "service_name"])

# Проверка неявных дубликатов в связке с user_id
# duplicates_check (cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"], keep=False

# Вывод на экран неявных дублткатов
# show_duplicates(cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"], keep=False, sort_cols='user_id') sort_cols=None, ascending=True по умолчанию

# Удаление дубликатов
# delete_duplicates(cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"], sort_cols='days_since_prev', ascending=False) sort_cols=None, ascending=True, keep='first' по умолчанию

# Проверка корректности удаления дубликатов
# duplicates_check (cols=["user_id", "order_ts", "revenue", "event_id", "tickets_count"]

# Вывод информации по столбцам object
# obj_info(cols=['device_type_canonical', 'event_type_main'], cols_top_tail = ['user_id', 'event_name', 'service_name', 'region_name', 'city_name'])

# Вывод инфо по числовым столбцам с гистограммами и боксплотами
# fig_info(cols=['tickets_count', 'days_since_prev', 'revenue_rub'], sub_plot_size = 6,1) edgecolor='white', color='skyblue'

# Фильтрация по 99му процентилю
# filtration(cols='revenue_rub', quant=0.99)

# вывод гистограммы и boxplot для выручки после фильтрации
# fig_info(cols='revenue_rub', sub_plot_size = 1,2) edgecolor='white', color='skyblue' 

# Вывод столбчатой диаграммы для tickets_count
# bar_plot(col='tickets_count') edgecolor='white', color='skyblue'

# Подсчеты отрицательной выручки
# neg_revenue_info(col='revenue_rub')

# Фильтрация отрицательной выручки
# neg_revenue_filt(col='revenue_rub')

# Вывод информации о количестве строк после предобработки
# cnt_df_after_filt()

# вывод гистограммы после фильтрации по отрицательным числам
# fig_info(cols='revenue_rub', sub_plot_size = 1,2) edgecolor='white', color='skyblue
