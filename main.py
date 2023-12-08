import streamlit as st
import pandas as pd
import numpy as np
import os
import psycopg2
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title = 'Báo cáo thực hiện doanh số bán ra kênh MT Đông Nam Bộ 1',layout = 'wide')


st.sidebar.title("Tải file CSV vào đây")

# Widget để upload file CSV
uploaded_file = st.sidebar.file_uploader("Chọn một file CSV", type=["csv"])

# Nếu người dùng đã upload một file CSV
if uploaded_file is not None:
    # Đọc dữ liệu từ file CSV thành DataFrame
    newfd = pd.read_csv(uploaded_file)
    newfd = newfd[newfd['Loại đơn'] == 'Đơn bán']

    
    # Tách tên khách ra thành các tên của hệ thống siêu thị
    newfd['Hệ thống ST'] = newfd['Tên KH'].str.split(' ')
    newfd['Hệ thống ST'] = newfd['Hệ thống ST'].agg(lambda x: x[0])
    newfd['Hệ thống ST'] = newfd['Hệ thống ST'].map({
        'BHX': 'Bách Hóa Xanh',
        'Coopfood': 'Sài Gòn Coop',
        'Coopmart': 'Sài Gòn Coop',
        'VMP': 'Vincommerce',
        'VM': 'Vincommerce',
        'Lotte': 'Lotte Mart',
        'MM': 'Mega Market',
        'BigC': 'BigC và Go!',
    })
    system_options = ['Tất cả'] + list(newfd['Hệ thống ST'].unique())
    sys = st.selectbox('Chọn hệ thống', system_options)

    

    startday, enddate = st.columns(2)
    with startday:
        startDate = pd.to_datetime(st.date_input('Từ ngày', value = pd.to_datetime(newfd['Ngày lấy đơn'], dayfirst = True).min()), dayfirst = True)
    with enddate:
        endDate = pd.to_datetime(st.date_input('Đến ngày', value = pd.to_datetime(newfd['Ngày lấy đơn'], dayfirst = True).max()), dayfirst = True)

    newfd = newfd[(pd.to_datetime(newfd['Ngày lấy đơn'], dayfirst = True) >= pd.to_datetime(startDate, dayfirst = True)) & (pd.to_datetime(newfd['Ngày lấy đơn'], dayfirst = True) <= pd.to_datetime(endDate, dayfirst = True))].copy()
    if sys == 'Tất cả':
        # Các chỉ số tổng quan (tổng doanh số,...)
        a1,b,c = st.columns(3)

        with a1:
            st.header('Tổng doanh số bán ra')
            st.subheader("{:,}".format(int(newfd['Thành tiền'].sum())) + ' VNĐ')
            st.markdown('''
                            <style>
                                span.e1nzilvr1{
                                    color: yellow;
                                    text-align: center;
                                }
                            </style>
                        ''', unsafe_allow_html = True)
        
        with c:
            st.header('Tổng sản lượng bán ra')
            st.subheader("{:,}".format(int(newfd['Hàng bán (Thùng)'].sum())) + ' Thùng')

        # Lọc ra chỉ lấy ngày tháng năm trong cột 'Ngày lấy đơn' sau đó group lại thành 1 nhóm
        newfd['Ngày tháng'] = pd.to_datetime(newfd['Ngày lấy đơn'], dayfirst = True).astype('str').astype('str')
        newfd['Ngày tháng'] = newfd['Ngày tháng'].str.split(' ')
        newfd['Ngày tháng'] = newfd['Ngày tháng'].agg(lambda x: x[0])
        newfd['Ngày tháng'] = pd.to_datetime(newfd['Ngày tháng'], dayfirst = True)
        a = newfd.groupby(newfd['Ngày tháng']).agg({'Thành tiền': 'sum'}).reset_index()

        # Vẽ biểu đồ đường thể hiện doanh số bán ra theo ngày trong năm 2023
        SBD = px.area(a, 'Ngày tháng', 'Thành tiền', title = 'Doanh số bán ra theo ngày  từ ' + str(startDate) + ' đến ' + str(endDate), labels={'Ngày tháng': 'Ngày tháng trong năm 2023', 'Thành tiền': 'Doanh số bán ra'})

        st.plotly_chart(SBD, use_container_width = True)

        # Lọc ra chỉ lấy tháng trong cột 'Ngày lấy đơn'
        newfd['Tháng'] = newfd['Ngày tháng'].astype('str')
        newfd['Tháng'] = newfd['Tháng'].str.split('-')
        newfd['Tháng'] = newfd['Tháng'].agg(lambda x: x[1])

        newfd['Tháng'] = newfd['Tháng'].map({
            '01': 'Tháng 01',
            '02': 'Tháng 02',
            '03': 'Tháng 03',
            '04': 'Tháng 04',
            '05': 'Tháng 05',
            '06': 'Tháng 06',
            '07': 'Tháng 07',
            '08': 'Tháng 08',
            '09': 'Tháng 09',
            '10': 'Tháng 10',
            '11': 'Tháng 11',
            '12': 'Tháng 12',
        })

        month, systems = st.columns(2)
        with month:
            # years = pd.to_datetime(newfd['Ngày lấy đơn']).apply(lambda x: x.year).astype('str')
            monthSale = newfd.groupby('Tháng').agg({'Thành tiền': 'sum'}).reset_index()
            SBM = px.bar(monthSale, 'Tháng', 'Thành tiền', title = 'Doanh số bán ra theo tháng từ ' + str(startDate) + ' đến ' + str(endDate), labels={'Tháng': 'Các tháng trong năm', 'Thành tiền': 'Doanh số bán ra'}, barmode = 'group')
            # , color = years

            st.plotly_chart(SBM, use_container_width = True)


        with systems:
            mtsystems = newfd.groupby('Hệ thống ST').agg({'Thành tiền': 'sum'}).reset_index()
            SBS = px.pie(names = mtsystems['Hệ thống ST'], values = mtsystems['Thành tiền'], hole=0.5, title = 'Tỷ lệ đóng góp của các hệ thống từ ' + str(startDate) + ' đến ' + str(endDate))

            st.plotly_chart(SBS, use_container_width = True)

        # Vẽ histogrram để biểu thị số đơn hàng tương ứng với mỗi giá trị đơn hàng
        PO = newfd.groupby('Mã đơn hàng').agg({'Thành tiền': 'sum'}).reset_index()
        xx = PO['Thành tiền'].value_counts().reset_index()
        xx.columns = ['Thành tiền', 'Số lượng đơn hàng']
        orders_code = px.histogram(xx, x='Thành tiền', y='Số lượng đơn hàng', labels = {'Số lượng đơn hàng': 'Số lượng đơn hàng', 'Thành tiền': 'Giá trị đơn hàng'}, title = 'Biểu đồ biểu thị số đơn hàng tương ứng với mỗi giá trị đơn hàng')
        st.plotly_chart(orders_code, use_container_width = True)
        
    else:
        df = newfd[newfd['Hệ thống ST'] == sys]
        
        st.header('Chi tiết tình hình bán ra của hệ thống ' + sys)
        # Các chỉ số tổng quan (tổng doanh số,...)
        a1,b,c = st.columns(3)
        with a1:
            st.header('Tổng doanh số bán ra')
            st.subheader("{:,}".format(int(df['Thành tiền'].sum())) + ' VNĐ')
            st.markdown('''
                            <style>
                                span.e1nzilvr1{
                                    color: yellow;
                                    text-align: center;
                                }
                            </style>
                        ''', unsafe_allow_html = True)
        with c:
            st.header('Tổng sản lượng bán ra')
            st.subheader("{:,}".format(int(df['Hàng bán (Thùng)'].sum())) + ' Thùng')

        # Lọc ra chỉ lấy ngày tháng năm trong cột 'Ngày lấy đơn' sau đó group lại thành 1 nhóm
        df['Ngày tháng'] = pd.to_datetime(df['Ngày lấy đơn'], dayfirst = True).astype('str')
        df['Ngày tháng'] = df['Ngày tháng'].str.split(' ')
        df['Ngày tháng'] = df['Ngày tháng'].agg(lambda x: x[0])
        df['Ngày tháng'] = pd.to_datetime(df['Ngày tháng'], dayfirst = True)
        a = df.groupby(df['Ngày tháng']).agg({'Thành tiền': 'sum'}).reset_index()

        # Vẽ biểu đồ đường thể hiện doanh số bán ra theo ngày trong năm 2023
        SBD = px.area(a, 'Ngày tháng', 'Thành tiền', title = 'Từ ' + str(startDate) + ' đến ' + str(endDate), labels={'Ngày tháng': 'Ngày tháng trong năm 2023', 'Thành tiền': 'Doanh số bán ra'})

        st.plotly_chart(SBD, use_container_width = True)

        # Lọc ra chỉ lấy tháng trong cột 'Ngày lấy đơn'
        df['Tháng'] = df['Ngày tháng'].astype('str')
        df['Tháng'] = df['Tháng'].str.split('-')
        df['Tháng'] = df['Tháng'].agg(lambda x: x[1])

        df['Tháng'] = df['Tháng'].map({
            '01': 'Tháng 01',
            '02': 'Tháng 02',
            '03': 'Tháng 03',
            '04': 'Tháng 04',
            '05': 'Tháng 05',
            '06': 'Tháng 06',
            '07': 'Tháng 07',
            '08': 'Tháng 08',
            '09': 'Tháng 09',
            '10': 'Tháng 10',
            '11': 'Tháng 11',
            '12': 'Tháng 12',
        })

        month, systems = st.columns(2)
        with month:
            # years = pd.to_datetime(df['Ngày lấy đơn']).apply(lambda x: x.year).astype('str')
            monthSale = df.groupby('Tháng').agg({'Thành tiền': 'sum'}).reset_index()
            SBM = px.bar(monthSale, 'Tháng', 'Thành tiền', title = 'Từ ' + str(startDate) + ' đến ' + str(endDate), labels={'Tháng': 'Các tháng trong năm', 'Thành tiền': 'Doanh số bán ra'})
            # , color = years

            st.plotly_chart(SBM, use_container_width = True)


        with systems:
            mtsystems = df.groupby('Hệ thống ST').agg({'Thành tiền': 'sum'}).reset_index()
            SBS = px.pie(names = mtsystems['Hệ thống ST'], values = mtsystems['Thành tiền'], hole=0.5, title = 'Tỷ lệ đóng góp của các hệ thống từ ' + str(startDate) + ' đến ' + str(endDate))

            st.plotly_chart(SBS, use_container_width = True)

         # Vẽ histogrram để biểu thị số đơn hàng tương ứng với mỗi giá trị đơn hàng
        PO = df.groupby('Mã đơn hàng').agg({'Thành tiền': 'sum'}).reset_index()
        order_filterd = PO['Thành tiền'].value_counts().reset_index()
        order_filterd.columns = ['Thành tiền', 'Số lượng đơn hàng']
        orders_code = px.histogram(order_filterd, x='Thành tiền', y='Số lượng đơn hàng', labels = {'Số lượng đơn hàng': 'Số lượng đơn hàng', 'Thành tiền': 'Giá trị đơn hàng'}, title = 'Biểu đồ biểu thị số đơn hàng tương ứng với mỗi giá trị đơn hàng của hệ thống ' + sys)
        st.plotly_chart(orders_code, use_container_width = True)
else:
    st.warning('Vui lòng upload file CSV')