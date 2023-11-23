#Packages:
#Database
import sqlite3 as sql
#load and save settings
import pickle
import os 
#UI/UX
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msgbox
#TTS(Text-To-Speech)
import pyttsx3 as tts
#Security
import secrets

#initializing
taxPercentage = 15
products = []
appname = "SaleSwift"
#Database
connection = sql.connect("Database.db")
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        description Text
    )
''')
connection.commit()
ttsEngine = tts.init()
#Variables, functions and classes 
class Product:
    def __init__(self, ID = 0,Name = "",Price =0,Description=""):
        self.ID = ID
        self.Name = Name
        self.Price = Price
        self.Description = Description
    def Tax(self):
        return (float(self.Price)*taxPercentage)/100
class Settings:
    def __init__(self, file_name='settings_data.pkl'):
        self.file_name = file_name
        self.data = {}
        self.load_settings_on_startup()
        self.ApplySettings()

    def update_setting(self, key, value):
        self.data[key] = value
        self.ApplySettings()
        
    def save_settings(self):
        with open(self.file_name, 'wb') as file:
            pickle.dump(self.data, file)

    def load_settings(self):
        try:
            with open(self.file_name, 'rb') as file:
                self.data = pickle.load(file)
                
        except (FileNotFoundError, pickle.UnpicklingError):
            print("Settings file not found or corrupted. Creating new settings.")
            self.create_default_settings()
        except Exception as e:
            print(f"An error occurred while loading settings: {str(e)}")

    def load_settings_on_startup(self):
        if os.path.exists(self.file_name):
            self.load_settings()
        else:
            print("Settings file not found. Creating new settings.")
            self.create_default_settings()
        self.ApplySettings()

    def create_default_settings(self):
        # Define your default settings here
        self.data = {
            "Theme":"System",
            "colour":"blue",
            "TTSVoice":0,
            "TTSRate":100,
            "TTSVolume":1
        }
        self.save_settings()
    def ApplySettings(self):
        ttsEngine.setProperty('rate', self.data["TTSRate"])
        ttsEngine.setProperty('volume',self.data["TTSVolume"])
        voices = ttsEngine.getProperty('voices')
        ttsEngine.setProperty('voice', voices[self.data["TTSVoice"]].id)
        ctk.set_appearance_mode(self.data["Theme"])
        ctk.set_default_color_theme(self.data["colour"])

settings = Settings()

def reportError(Error):
    ttsEngine.stop()
    ttsEngine.say(f"Error we have encountered the following error, {Error}")
    while ttsEngine.runAndWait():
        msgbox.showerror("Error",f"Error:{Error}")

#Window
win = ctk.CTk()
win.title(appname)
#Table Of Products
TableOfProducts = ttk.Treeview(win, columns=["Name","Price","Tax", "Description", "ID"])
TableOfProducts.grid(row = 0,column= 0,columnspan=3)
TableOfProducts.heading("Name",text="Name")
TableOfProducts.heading("Price",text="Price(N$)")
TableOfProducts.heading("Tax",text=f"tax({taxPercentage}% of Price)")
TableOfProducts.heading("Description",text="Description")
TableOfProducts.heading("ID",text="ID")

TableOfProducts.column("Name", width= 200)
TableOfProducts.column("#0",width=0)
TableOfProducts.column("Price", width= 60)
TableOfProducts.column("Tax", width= 160)
TableOfProducts.column("Description", width= 120)
TableOfProducts.column("ID", width= 60)
"""
with open('p.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        print(line)
        product_info = line.strip().split('-')
        product_name = product_info[0]
        price = product_info[1]
        description = product_info[2]
        # Insert data into the products table
        cursor.execute("INSERT INTO products (name, price,description) VALUES (?, ?, ?)",
                    (product_name, float(price), description))
connection.commit()
"""
#add Products
def AddProduct():
    AddProductWin = ctk.CTkToplevel()
    NameEntry = ctk.CTkEntry(AddProductWin,placeholder_text="Name:")
    NameEntry.grid(row = 0, column = 0)
    PriceEntry = ctk.CTkEntry(AddProductWin,placeholder_text="Price:")
    PriceEntry.grid(row = 1, column = 0)
    DescriptionEntry = ctk.CTkEntry(AddProductWin,placeholder_text="Description(optional):")
    DescriptionEntry.grid(row = 2, column = 0)
    def submit():
        name = NameEntry.get()
        Description = DescriptionEntry.get()
        isPriceValid = True
        try:
            priceV2 = float(PriceEntry.get())
            #You may be wondering why im using secrets rather than "==", its because "==" is vulnerable to timing attacks
        except ValueError:
            isPriceValid = False
        except Exception as e:
            msgbox.showerror("Error",e)

        if isPriceValid:
            if secrets.compare_digest(name,""):
                reportError("Name field may not be empty")
            else:
                isNameValid = True
                for product in products:
                    if product.Name == name:
                        isNameValid = False
                        break
                if isNameValid:
                    cursor.execute('INSERT INTO products (name, price,description) VALUES (?, ?,?)', (name, priceV2,Description))
                    connection.commit()
                    prod = Product(cursor.lastrowid,name,priceV2,Description)
                    products.append(prod)
                    TableOfProducts.insert("", tk.END, values=(name, priceV2, prod.Tax(),Description,cursor.lastrowid))  # Parent item
                    AddProductWin.destroy()
                else:
                    reportError("","Product shounld not share names with other products.")

    SubmitBtn = ctk.CTkButton(AddProductWin,text="Submit",command=lambda:submit())
    SubmitBtn.grid(row = 3, column = 0)
APBtn = ctk.CTkButton(win,text="Add Product",command=lambda:AddProduct())
APBtn.grid(row = 1, column= 0)
#Delete Product
def DeleteProduct():
    selected_row = TableOfProducts.selection()
    if selected_row:
        confirmation = msgbox.askyesno("Delete Product","Are you sure you want to delete this product?")
        if confirmation:
            # Get the values of the selected item
            values = TableOfProducts.item(selected_row)['values']
            
            # Delete the item from the Treeview
            TableOfProducts.delete(selected_row)
            
            # If needed, perform deletion from the SQLite database
            # Assuming 'user_id' is the first value in the values list
            user_id = int(values[4])
            name = values[0]
            # Delete the row from the database
            for product in products:
                if product.ID == user_id:
                    products.remove(product)
                    break  # Exit loop once the user is removed

            cursor.execute("DELETE FROM Products WHERE id=? and name=?", (user_id,name))
            
            connection.commit()
    else:
        msgbox.showinfo("Title","Please select a row first.")
DPBtn = ctk.CTkButton(win,text="Delete product",command=lambda:DeleteProduct())
DPBtn.grid(row = 1,column = 1)
#edit Product
def EditProduct():
    selected_row = TableOfProducts.selection()
    if selected_row:
        # Get the values of the selected item
        values = TableOfProducts.item(selected_row)['values']
        
        # If needed, perform deletion from the SQLite database
        # Assuming 'user_id' is the first value in the values list
        user_id = int(values[4])
        EditProductWin = ctk.CTkToplevel()
        NameEntry = ctk.CTkEntry(EditProductWin,placeholder_text="Name:")
        NameEntry.grid(row = 0, column = 0)
        PriceEntry = ctk.CTkEntry(EditProductWin,placeholder_text="Price:")
        PriceEntry.grid(row = 1, column = 0)
        DescriptionEntry = ctk.CTkEntry(EditProductWin,placeholder_text="Description(optional):")
        DescriptionEntry.grid(row = 2, column = 0)
        def submit():
            name = NameEntry.get()
            priceV1 = PriceEntry.get()
            Description = DescriptionEntry.get()
            try:
                priceV2 = float(priceV1)
                #You may be wondering why im using secrets rather than "==", its because "==" is vulnerable to timing attacks
                if secrets.compare_digest(name,""):
                    reportError("Name field may not be empty")
                else:
                    isNameValid = True
                    for product in products:
                        if secrets.compare_digest(product.Name,name):
                            isNameValid = False
                            break
                    if isNameValid:
                        cursor.execute('''
                        UPDATE Products SET name = ?, price = ?, description = ? WHERE id = ?
                        ''', (name,priceV2,Description, user_id))
                        connection.commit()
                        prod = Product(user_id,name,priceV2,Description)
                        TableOfProducts.item(selected_row,values=(prod.Name,prod.Price,prod.Tax(),prod.Description,prod.ID))
                        for product in products:
                            if product.ID == user_id:
                                product = prod
                                break  # Exit loop once the user is removed
                        EditProductWin.destroy()
                    else:
                        reportError("Product should not share names with other products.")
            except ValueError:
                reportError("Invalid value for price please ensure it is a decimal or integer")
        SubmitBtn = ctk.CTkButton(EditProductWin,text="Submit",command=lambda:submit())
        SubmitBtn.grid(row = 3, column = 0)
    else:
        msgbox.showinfo("Title","Please select a row first.")
EPBtn = ctk.CTkButton(win,text="Edit product",command=lambda:EditProduct())
EPBtn.grid(row = 1,column = 2)
# start code
cursor.execute('SELECT * FROM Products')
rows = cursor.fetchall()
for row in rows:
    prod = Product(row[0],row[1],row[2],row[3])
    products.append(prod)
    TableOfProducts.insert("", tk.END, values=(prod.Name, prod.Price, prod.Tax(),prod.Description,prod.ID))

def SettingsMenu():
    SettingsWinContainer = ctk.CTkToplevel()
    SettingsWinContainer.title("Settings")
    SettingsWin = ctk.CTkScrollableFrame(SettingsWinContainer)
    SettingsWin.pack(fill = tk.BOTH,expand = True)

    def ThemeChange(newTheme : str):
        settings.update_setting("Theme",newTheme)
    ThemeHeader = ctk.CTkLabel(SettingsWin,text="Theme:",font=("Arial Rounded MT Bold",24))
    ThemeHeader.grid(row = 0,column = 0)
    ThemeDropVar = ctk.StringVar(SettingsWin)
    ThemeDropDown = ctk.CTkOptionMenu(SettingsWin,variable=ThemeDropVar,values=["system","dark","light"],command=ThemeChange)
    ThemeDropVar.set(settings.data["Theme"])
    ThemeDropDown.grid(row = 1,column = 0)

    def ColourChange(newColour : str):
        if newColour =="dark blue":
            settings.update_setting("colour", "dark-blue")
        else:
            settings.update_setting("colour", newColour)
    ColourHeader = ctk.CTkLabel(SettingsWin,text="Accent Colour:",font=("Arial Rounded MT Bold",24))
    ColourHeader.grid(row = 2,column = 0)
    ColourDropVar = ctk.StringVar(SettingsWin)
    ColourDropDown = ctk.CTkOptionMenu(SettingsWin,variable=ColourDropVar,values=["blue","dark blue","green"],command=ColourChange)
    ColourDropVar.set(settings.data["colour"])
    ColourDropDown.grid(row = 3,column = 0)

    TTSHeader = ctk.CTkLabel(SettingsWin,text="TTS(Text-To-Speech) configuration:",font=("Arial Rounded MT Bold",24))
    TTSHeader.grid(row = 4,column = 0)

    def VoiceChange(newVoice : str):
        if newVoice == "Male":
            settings.update_setting("TTSVoice", 0)
        elif newVoice == "Female":
            settings.update_setting("TTSVoice", 1)
    VoiceHeader = ctk.CTkLabel(SettingsWin,text="Voice:",font=("Arial Rounded MT Bold",24))
    VoiceHeader.grid(row = 5,column = 0)
    VoiceDropVar = ctk.StringVar(SettingsWin)
    VoiceDropDown = ctk.CTkOptionMenu(SettingsWin,variable=VoiceDropVar,values=["Male","Female"],command=VoiceChange)
    if settings.data["TTSVoice"] == 0:
        VoiceDropVar.set("Male")
    elif settings.data["TTSVoice"] == 1:
        VoiceDropVar.set("Female")
    VoiceDropDown.grid(row = 6,column = 0)

    def RateChange(newRate : int):
        settings.update_setting("TTSRate", newRate)
    RateHeader = ctk.CTkLabel(SettingsWin,text="Rate:",font=("Arial Rounded MT Bold",24))
    RateHeader.grid(row = 7,column = 0)
    RateDropDown = ctk.CTkSlider(SettingsWin,from_=30,to=200,command=RateChange,)
    RateDropDown.grid(row = 8,column = 0)
    RateDropDown.set(settings.data["TTSRate"])

    def VolumeChange(newVolume : int):
        settings.update_setting("TTSVolume", newVolume/100)
    VolumeHeader = ctk.CTkLabel(SettingsWin,text="Volume:",font=("Arial Rounded MT Bold",24))
    VolumeHeader.grid(row = 9,column = 0)
    VolumeDropDown = ctk.CTkSlider(SettingsWin,from_=0,to=100,command=VolumeChange)
    VolumeDropDown.grid(row = 10,column = 0)
    RateDropDown.set(settings.data["TTSVolume"])
    def TestVoice():
        ttsEngine.say("This is what the voice sounds like.")
        ttsEngine.runAndWait()
    testvoicebtn = ctk.CTkButton(SettingsWin,text="Test Voice",command=lambda:TestVoice())
    testvoicebtn.grid(row = 11,column = 0)
#Checkout 
def Checkout():
    class cartItem:
        def __init__(self,product = None,quantity = 1):
            self.product = product if product is not None else Product()
            self.quantity = quantity
        def QxP(self):
            return self.quantity * self.product.Price
        def TxQ(self):
            return self.quantity * self.product.Tax()
    cart = []
    CheckoutWin = ctk.CTkToplevel()
    CheckoutWin.focus()
    CheckoutWin.resizable(False,False)
    CheckoutWin.title("Checkout")
    CartFrame = ctk.CTkScrollableFrame(CheckoutWin,width=820)
    CartFrame.grid(row =0,column = 0,columnspan = 3)
    CartTable = ttk.Treeview(CartFrame, columns=["ID","Name","Price","Quantity","T","TxQ","PxQ"])
    CartTable.pack(expand=True, fill=tk.BOTH)
    CartTable.heading("ID", text= "Product ID")
    CartTable.heading("Name",text="Product Name")
    CartTable.heading("Price", text= "Price(N$)")
    CartTable.heading("Quantity", text= "Quantity")
    CartTable.heading("T",text="Tax")
    CartTable.heading("TxQ", text="Tax*Quantity")
    CartTable.heading("PxQ", text= "Price*Quantity")

    CartTable.column("#0",width= 0)
    CartTable.column("ID",width=100)
    CartTable.column("Name",width= 200)
    CartTable.column("Price",width=  100)
    CartTable.column("Quantity",width= 100)
    CartTable.column("T",width= 100)
    CartTable.column("TxQ",width= 100)
    CartTable.column("PxQ",width= 100)

    TotA = ctk.DoubleVar()
    TotA.set(0.0)
    TaxA = ctk.DoubleVar()
    TaxA.set(0.0)
    info = ctk.CTkScrollableFrame(CheckoutWin)
    info.grid(row = 0,column = 3)
    TotalHeader = ctk.CTkLabel(info,text="Total:",font=("Arial Rounded MT Bold",24))
    TotalHeader.grid(row = 0,column = 0)
    TotalAdition = ctk.CTkLabel(info,text="N$0.0")
    TotalAdition.grid(row =1,column = 0, sticky='w')
    TaxHeader = ctk.CTkLabel(info,text="Tax:",font=("Arial Rounded MT Bold",24))
    TaxHeader.grid(row = 2,column = 0)
    TaxAdition = ctk.CTkLabel(info,text="N$0.0")
    TaxAdition.grid(row =3,column = 0, sticky='w')
    ChangeCalculaterHeader = ctk.CTkLabel(info,text="Change Calculator:",font=("Arial Rounded MT Bold",24))
    ChangeCalculaterHeader.grid(row = 4,column = 0)
    AmountTenderedEntry = ctk.CTkEntry(info,placeholder_text="The Amount Tendered:")
    AmountTenderedEntry.grid(row = 5,column = 0)
    def Submit():
        total = TotA.get()
        AmountTV1 = AmountTenderedEntry.get()
        try:
            AmountTV2 = float(AmountTV1)
            if AmountTV2 >= total:
                change = AmountTV2-total

                ChangeWin = ctk.CTkToplevel()
                ChangeWin.title("Change")
                ChangeText = ctk.CTkLabel(ChangeWin,text=f"Money Tendered- Total = Change\nN${AmountTV2}-N${total}=N${change}")
                ChangeText.grid(row =0,column = 0)

            else:
                msgbox.showerror("Error","Not enough money was tendered")
        except ValueError:
            msgbox.showerror("Error","Please enter a valid number")
    SubmitBtn = ctk.CTkButton(info,text = "Submit",command=lambda:Submit())
    SubmitBtn.grid(row =6,column=0)
    def refreshCart():
        CartTable.delete(*CartTable.get_children())
        
        price = 0.0
        Tax =0.0
        for CI in cart:
            CartTable.insert("",tk.END,values=(CI.product.ID,CI.product.Name,CI.product.Price,CI.quantity,CI.product.Tax(),CI.TxQ(),CI.QxP()))
            price += CI.product.Price*CI.quantity
            
            Tax += CI.product.Tax()
        TotA.set(price)
        TaxA.set(Tax)
        TotalAdition.configure(text=f"N${TotA.get()}")
        TaxAdition.configure(text = f"N${TaxA.get()}")
        
       
    def AddProductToCart():
        nonlocal CheckoutWin
        APTCW = ctk.CTkToplevel()
        APTCW.focus()
        APTCW.resizable(False,False)
        APTCW.title = "Add Product To Cart"
        productsNamesList = []
        for product in products:
            prodname = product.Name
            productsNamesList.append(prodname)
        if len(productsNamesList) ==0:
            msgbox.showinfo("Title","Please add products first")
            APTCW.destroy()
        else:
            selectedProduct=products[0]
            def selectProd(prod : str):
                nonlocal selectedProduct
                for produc in products:
                    if secrets.compare_digest(produc.Name,prod):
                        selectedProduct = produc
                        break
            prodlabel = ctk.CTkLabel(APTCW,text="Product:")
            prodlabel.grid(row =0,column = 0)
            productsDropDown = ctk.CTkOptionMenu(APTCW,values=productsNamesList,command=selectProd)
            productsDropDown.grid(row =1,column = 0)
            productsDropDown.set(productsNamesList[0])
            Quantityentry = ctk.CTkEntry(APTCW,placeholder_text="Quantity:")
            Quantityentry.grid(row = 2, column = 0)
            def Submit():
                nonlocal selectedProduct
                CINameValid = True
                for CI in cart:
                    if CI.product.Name == selectedProduct.Name:
                        CINameValid = False

                if CINameValid:
                    quanV1 = Quantityentry.get()
                    try:
                        quanV2 = int(quanV1)
                        CI = cartItem(selectedProduct,quanV2)
                        cart.append(CI)
                        CartTable.insert("",tk.END,values=(CI.product.ID,CI.product.Name,CI.product.Price,CI.quantity,CI.product.Tax(),CI.TxQ(),CI.QxP()))
                        APTCW.destroy()
                        refreshCart()
                    except ValueError:
                        reportError("Quantity must be Integer")
                else:
                    msgbox.showerror("Error",f"Selected product, {selectedProduct.Name}, is already in cart if you want to edit the product first select its row then press 'Edit Cart Item.'")
            SubmitBtn = ctk.CTkButton(APTCW,text="Submit",command=lambda:Submit())
            SubmitBtn.grid(row = 3,column = 0)
        screen_width = APTCW.winfo_screenwidth()
        screen_height = APTCW.winfo_screenheight()

        x_coordinate = (screen_width - APTCW._current_width) // 2
        y_coordinate = (screen_height - APTCW._current_height) // 2
        APTCW.geometry(f"{APTCW._current_width}x{APTCW._current_height}+{x_coordinate}+{y_coordinate}")
    def RemoveproductFromCart():
        selectedrow = CartTable.selection()
        if selectedrow:
            yn = msgbox.askyesno("Delete Cart Item", "Are ypu sure you want to delete cart Item?")
            if yn:
                vals = CartTable.item(selectedrow)['values']
                CartTable.delete(selectedrow)
                ciname = vals[1]
                for CI in cart:
                    if CI.product.Name ==ciname:
                        cart.remove(CI)
                        break
                refreshCart()
        else:
            msgbox.showerror("Select product first")
    def EditProductInCart():
        selectedrow = CartTable.selection()
        if selectedrow:
            NQW = ctk.CTkToplevel()
            NQE = ctk.CTkEntry(NQW,placeholder_text="New Quantity:")
            NQE.grid(row =0,column = 0)
            values = CartTable.item(selectedrow)["values"]
            def submit():
                NQV1 = NQE.get()
                try:
                    NQV2 = int(NQV1)
                    if NQV2 == 0:
                        msgbox.showerror("Error","New Quantity mist be more than 0.")
                    else:
                        for CI in cart:
                            if CI.product.Name == values[1]:
                                CI.quantity = NQV2
                                break
                        refreshCart()
                        NQW.destroy()
                        
                except ValueError:
                    msgbox.showerror("","New Quantity must be integer")
            SubmitBtn = ctk.CTkButton(NQW,text="Submit",command=lambda:submit())
            SubmitBtn.grid(row =1,column = 0)
            refreshCart()
    APTCBtn = ctk.CTkButton(CheckoutWin,text="Add Product to Cart",command=lambda:AddProductToCart())
    APTCBtn.grid(row =1,column = 0)
    RPFCBtn = ctk.CTkButton(CheckoutWin,text="Remove Product from Cart",command=lambda:RemoveproductFromCart())
    RPFCBtn.grid(row =1,column = 1)
    EPICBtn = ctk.CTkButton(CheckoutWin,text="Edit Product in Cart",command=lambda:EditProductInCart())
    EPICBtn.grid(row =1,column = 2)
    
settings.ApplySettings() 
    
CheckoutBtn = ctk.CTkButton(win,text="Checkout",command=lambda:Checkout())
CheckoutBtn.grid(row =0,column= 4)
SettingsBtn = ctk.CTkButton(win,text="Settings",command=lambda:SettingsMenu())
SettingsBtn.grid(row = 1,column = 4)
#ttsEngine.say(f"Welcome to {appname}")
ttsEngine.runAndWait()
win.mainloop()

#mid code

#end code
ttsEngine.stop()
connection.commit()
connection.close
