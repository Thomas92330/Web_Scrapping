import tkinter as tk
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from selenium import webdriver
from matplotlib import style
import pandas as pd
import csv
from threading import Thread
from sklearn.svm import SVR
import numpy as np 
from sklearn.model_selection import train_test_split

#Initialisation of the window
app = tk.Tk()

#Initialisation of global variable used in threads
update_prediction = False
update_legend = False
activate_scrap = False

#configuration of a grid setting
app.columnconfigure(0, weight=1)
app.columnconfigure(1, weight=1)

app.rowconfigure(0, weight=1)
app.rowconfigure(1, weight=3)
app.rowconfigure(2, weight=1)

#Initialisation of the driver
driver = webdriver.Chrome("D:\chromedriver.exe")
driver.get('https://www.boursorama.com/bourse/devises/taux-de-change-bitcoin-euro-BTC-EUR/')

#Check if the necessary .csv files are existing and create them if not
def init_csv_files():
    try:
        #We try to read the file Data_csv_temp.csv
        with open('Data_csv_temp.csv','r') as csvfile:
            test = csvfile.read()
    except IOError:
        #We create the file  Data_csv_temp.csv
        with open('Data_csv_temp.csv','w',newline='') as csvfile:
            column_names = ['row',"ouv","high","low","last","var","vol",'time','value']
            writer = csv.DictWriter(csvfile,fieldnames = column_names)
            writer.writeheader()
    
    try:
        #We try to read the file Data_csv.csv
        with open('Data_csv.csv','r') as csvfile:
            test = csvfile.read()
    except IOError:
        #We create the file  Data_csv_temp.csv
        with open('Data_csv.csv','w',newline='') as csvfile:
            column_names = ['row',"ouv","high","low","last","var","vol",'time','value']
            writer = csv.DictWriter(csvfile,fieldnames = column_names)
            writer.writeheader()

#Overwright the current Data_csv_temp.csv file with a single new row    
def init_data_csv_temp():
    ouv,high,low,last,var,vol,time_bitcoin,value = get_bitcoin()
    data = {'row' : 'row',
            'ouv' : ouv,
            'high' : high,
            'low' : low,
            'last' : last,
            'var' : var,
            'vol' : vol,
            'time' : time_bitcoin,
            'value' : value}
    
    with open('Data_csv_temp.csv','w',newline='') as csvfile:
        column_names = ['row',"ouv","high","low","last","var","vol",'time','value']
        writer = csv.DictWriter(csvfile,fieldnames = column_names)
        writer.writeheader()
        writer.writerow(data)
    time.sleep(1)

#Set the legend label with the last row of Data_temp_csv.csv
def init_legend():
    df = pd.read_csv("Data_csv_temp.csv")
    str_to_load = "Ouv: " + str(df.iloc[-1]["ouv"]) + "\n High: " + str(df.iloc[-1]["high"]) + "\n Low: " + str(df.iloc[-1]["low"]) + "\n Last: " + str(df.iloc[-1]["last"]) + "\n Var: " + str(df.iloc[-1]["var"]) + "\n Value: " + str(df.iloc[-1]["value"])
    label_for_legend.configure(text = str_to_load)
      
#scrap the website and retrieve the necessary datas
def get_bitcoin():
    #Sometime the request will fail and retrieve an empty element
    #If it does, we by pass the error by retrieving the previous datas
    try:
        elements = driver.find_elements_by_class_name("c-quote-chart-info-area__value")
        ouv = float(elements[0].text) 
        high = float(elements[1].text)  
        low = float(elements[2].text)  
        last = float(elements[3].text)  
        var = float(elements[4].text.strip('%'))
        vol = float(elements[5].text)  
        
        element = driver.find_element_by_css_selector("#main-content > div > section.l-quotepage > header > div > div > div.c-faceplate__company > div.c-faceplate__info > div > div.c-faceplate__price.c-faceplate__price--inline > span.c-instrument.c-instrument--last")
        value = float(element.text.replace(" ","")) #There is a space in the number, removing it make it easier when we want to cast it as a float
        time_bitcoin = time.time()
        return  ouv,high,low,last,var,vol,time_bitcoin,value
    except ValueError:
        df = pd.read_csv("Data_csv_temp.csv")
        ouv = df["ouv"].iloc[-1]
        high = df["high"].iloc[-1]
        low = df["low"].iloc[-1] 
        last = df["last"].iloc[-1]
        var = df["var"].iloc[-1]
        vol = df["vol"].iloc[-1] 
        time_bitcoin = time.time()
        value = df["value"].iloc[-1]
        return  ouv,high,low,last,var,vol,time_bitcoin,value

#fonction bind to the button activating scrap
def on_click_button_activating_scrap(event):
    global activate_scrap
    if activate_scrap:
        activate_scrap = False
        button_activating_scrap.configure(text="Activate scrap")
    else:
        activate_scrap = True
        button_activating_scrap.configure(text="Stop scrapping")
        global thread_activate_scrap
        thread_activate_scrap = Thread(target=scrap_thread)
        thread_activate_scrap.start()

#this fonction allow us to end the thread by changing the value of the global variable activate_scrap
def scrap_thread():
    global activate_scrap
    while True:
        if activate_scrap:
            write_values_in_csv()
        else:
            break

#write new datas in a csv file and retrieve them via the get_bitcoin function
def write_values_in_csv():
    temps = int(time.time())
    temps += 15
    driver.refresh() #To get the "value" we have to refresh the page 
    time.sleep(5) #let time for the driver to refresh
    ouv,high,low,last,var,vol,time_bitcoin,value = get_bitcoin()
    
    #Put a 15secondes timer (taking into acount the time for the request and refresh) betweeen each new request
    while(int(time.time()) != temps):
        pass
 
    data = {'row' : [ouv, high, low, last ,var, vol, time_bitcoin, value]}
    data_to_load = pd.DataFrame.from_dict(data,orient="index")
    
    filename = "Data_csv_temp.csv"
    with open(filename,'a') as df:
        data_to_load.to_csv(df,header=False)
    
#fonction bind to the button updating legend  
def on_click_button_updating_legend(event):
    global update_legend
    if update_legend:
        update_legend = False
        button_updating_legend.configure(text="Update")
    else:
        update_legend = True
        button_updating_legend.configure(text="Stop Updating")
        global thread_updating_legend
        thread_updating_legend = Thread(target=refresh_legend)
        thread_updating_legend.start()

#refresh the legend by retrieving the last row from the data_csv_temp.csv file
def refresh_legend():
    global update_legend    
    if not update_legend:
        return
    df = pd.read_csv("Data_csv_temp.csv")
    str_to_load = "Ouv: " + str(df.iloc[-1]["ouv"]) + "\n High: " + str(df.iloc[-1]["high"]) + "\n Low: " + str(df.iloc[-1]["low"]) + "\n Last: " + str(df.iloc[-1]["last"]) + "\n Var: " + str(df.iloc[-1]["var"]) + "\n Value: " + str(df.iloc[-1]["value"])
    label_for_legend.configure(text = str_to_load)
    
    app.after(ms=10000,func=refresh_legend)

#fonction bind to the button predict  
def on_click_button_predict(event):
    global update_prediction
    if update_prediction:
        update_prediction = False
        button_predict.configure(text="Give prediction")
    else:
        update_prediction = True
        button_predict.configure(text="Stop giving prediction")
        global thread_predict
        thread_predict = Thread(target=refresh_prediction)
        thread_predict.start()
        
#launch a new prediction from the predictor function and change the text accordingly
def refresh_prediction():
    global update_prediction   
    if not update_prediction:
        return
    df = pd.read_csv("Data_csv_temp.csv")
    accuracy , prediction = predictor()
    str_to_load = "Accuracy: " + str(accuracy) + "\nPrediction: " + str(prediction)
    if (df.iloc[-1]["value"] < prediction):
        str_to_load += "  -Buy"
    elif (df.iloc[-1]["value"] > prediction):
        str_to_load += "  -Sell"
    else:
        str_to_load +="  -Undetermined"
    label_for_prediction.configure(text = str_to_load)
        
    app.after(ms=10000,func=refresh_prediction)
    
#Use the data_csv file to train
#make a prediction from the data_csv_temp file
#use the SVR fonction from sklearn library
#return accuracy on the training set (Data_csv) and prediction on the ongoing dataset (Data_csv_temp)
def predictor():
    big_df= pd.read_csv("Data_csv.csv", error_bad_lines=False)
    current_df = pd.read_csv("Data_csv_temp.csv", error_bad_lines=False)
    
    df=pd.DataFrame()
    df["value"] = big_df["value"]
    df['prediction'] = big_df['value'].shift(-1)
    
    df_prediction = pd.DataFrame()
    df_prediction["value"] = current_df["value"]
    df_prediction['prediction'] = current_df['value'].shift(-1)
    
    X = np.array(df.drop(['prediction'],1))
    X = X[:len(df)-1]
    
    y = np.array(df['prediction'])
    y = y[:-1]
    
    prediction = np.array(df_prediction.drop(['prediction'],1))[-1:]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.00001)#Create the model
    svr_rbf.fit(X_train, y_train) #Train the model
    
    svr_rbf_confidence = svr_rbf.score(X_test, y_test)
    
    svm_prediction = svr_rbf.predict(prediction)

    return svr_rbf_confidence, svm_prediction

#fonction bind to the button saving
def on_click_button_saving_csv(event):
    data_to_load = pd.read_csv("Data_csv_temp.csv")
    filename = "Data_csv.csv"
    with open(filename,'a') as df:
        data_to_load.to_csv(df,header=False)
    init_data_csv_temp()

#fonction bind to the button quit
#close everything befor destroying the app
def on_click_button_quit(event):
    driver.quit()
    
    global update_prediction 
    global update_legend 
    global activate_scrap 
    
    update_prediction = False
    update_legend = False
    activate_scrap = False

    app.destroy()
    
#update the graph with the last row from data_csv_temp
def update_graph(dt):
    df = pd.read_csv("Data_csv_temp.csv")
    x=[i for i in range(len(df['ouv']))]
    ax1.clear()
    ax2.clear()

    ax1.set_ylabel('Euros', color='b')
    ax2.set_ylabel('%', color='b')
    
    ax1.plot(x,df['value'], 'b-o',label='Valeur')
    ax1.xaxis.set_ticklabels([])
    ax1.legend(loc='upper left')
    
    if(df.iloc[-1]["var"] > 0):
        ax2.plot(x,df['var'], 'g-o',label='Variation')
    else:
        ax2.plot(x,df['var'], 'r-o',label='Variation')
    ax2.legend(loc='upper left')

init_csv_files()
init_data_csv_temp()

#Initialisation of the different elements of our app
frame_top_left = tk.Frame(app)

button_activating_scrap = tk.Button(frame_top_left , text="Activate scrap") 

button_saving_csv = tk.Button(frame_top_left, text="Save") 
button_quit= tk.Button(frame_top_left, text='Quit')

frame_top_left.grid(column=0, row=0, sticky="nsew")
button_activating_scrap.pack()
button_saving_csv.pack(side="right")
button_quit.pack(side="left")

button_updating_legend = tk.Button(text="Updating legends") 
button_updating_legend.grid(column=1, row=0)

button_predict = tk.Button(text="Give prediction") 
button_predict.grid(column=0, row=3)

label_for_legend = tk.Label(app, text=" ")
label_for_legend.grid(column=1, row=1)
init_legend()

label_for_prediction = tk.Label(app, text=" ")
label_for_prediction.grid(column=1, row=2)


fig = Figure(figsize=(4,2), dpi=100)
canvas = FigureCanvasTkAgg(fig,app)
canvas.get_tk_widget().grid(column=0, row=1)  

#Initialisation of our graph
style.use("ggplot")
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212, sharex=ax1)
ax2.set_xlabel('Temps')
ax1.set_ylabel('Euros', color='b')
ax2.set_ylabel('%', color='r')
ani = FuncAnimation(fig, update_graph, interval=8000)

#Initialisation of our bindings
button_quit.bind("<ButtonRelease-1>", on_click_button_quit)
button_activating_scrap.bind("<ButtonRelease-1>", on_click_button_activating_scrap)
button_saving_csv.bind("<ButtonRelease-1>", on_click_button_saving_csv)
button_updating_legend.bind("<ButtonRelease-1>", on_click_button_updating_legend)
button_predict.bind("<ButtonRelease-1>", on_click_button_predict)

app.mainloop()
