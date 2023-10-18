import requests
from bs4 import BeautifulSoup
import time
from faker import Faker
import json
import csv
import pandas as pd
fake=Faker()

# This captures the entire data that is extracted page by page
data={}
page_no=1

link="https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_1"

def get_response(link,headers,page_no):
    r = requests.get(link,headers=headers) 
    try:
        soup = BeautifulSoup(r.content, 'html.parser')
        x_all=soup.find_all('div',attrs={"data-component-type": "s-search-result"})
        if x_all!=[]:
            print("success")
            get_data(soup,page_no)
            next_link=soup.find('a',attrs={"class": "s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"})
            if(next_link and page_no<21):
                link=f"https://www.amazon.in{next_link['href']}"
                headers={
                    'Accept':"*/*",
                'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'en-US,en;q=0.9',
                'User-Agent':fake.user_agent()
                }
                page_no+=1
                get_response(link,headers,page_no)
        else:
            print("retrying...")
            headers={
                'Accept':"*/*",
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'User-Agent':fake.user_agent()
            }
            get_response(link,headers,page_no)
    except:
        print("retrying.......")
        headers={
                'Accept':"*/*",
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'User-Agent':fake.user_agent()
            }
        get_response(link,headers,page_no)

def get_data(soup,page_no):
    s = soup.find('div', class_="s-main-slot s-result-list s-search-results sg-row")
    x_all=soup.find_all('div',attrs={"data-component-type": "s-search-result"})
    page_content=[]
    for x in x_all:
        temp={}
        temp['link']=f"https://www.amazon.in{x.find('a',attrs={'class':'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})['href']}"
        temp['prod_name']=x.find('span',class_="a-size-medium a-color-base a-text-normal").text
        temp['price']=x.find('span',class_="a-offscreen").text
        temp['rating']=x.find('span',class_="a-icon-alt").text
        temp['total_reviews']=x.find('span',class_="a-size-base s-underline-text").text
        page_content.append(temp)
    data[page_no]=page_content

headers={
            'User-Agent': fake.user_agent(),
            'Accept-Language': 'en-US,en;q=0.9'
        }
get_response(link,headers,1)
# By now we have got data of products page by page

# We are combining all products into a single big data field
temp=[]
for page in data:
    for i in data[page]:
        temp.append(i)
data=temp

# Now we get product details for each product by visiting the link
def get_prod_details(link,headers,i):
    r=requests.get(link,headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser') 
    title=soup.find("span",attrs={"id":"productTitle"})
    if("For automated access to price change or offer listing change events" not in r.text and title!=None):
        x={}
        try:
            features_list=soup.find('div',attrs={"class": "a-section a-spacing-medium a-spacing-top-small"}).find_all('li')
        except:
            features_list=soup.find("div",attrs={"id":"productFactsDesktop_feature_div"}).find_all("li")
        prod_description=''
        for list in features_list:
           prod_description+=list.text
        x['productDescription']=prod_description
        x['asin']=soup.find(id='averageCustomerReviews').get('data-asin')
        try:
            manufacturer=soup.find(id="bylineInfo_feature_div").text.strip().replace("Brand:","").replace("Visit the ","")
        except:
            manufacturer=""
        x['manufacturer']=manufacturer
        for item in x:
            data[i][item]=x[item]
    else:
        print("retrying..........")
        headers={
            'Accept':"*/*",
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'User-Agent':fake.user_agent()
        }
        get_prod_details(link,headers,i)   
    
for i in range(len(data)):
    prod=data[i]
    headers={
        'Accept':"*/*",
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-US,en;q=0.9',
        'User-Agent':fake.user_agent()
    }
    link=prod['link']
    get_prod_details(link,headers,i)
    print(f"Product-{i+1} extraction completed")
    
# Now the data will be converted to a CSV file
json_data=data
csv_file = 'products.csv'

headers = ['link', 'prod_name', 'price', 'rating', 'total_reviews','productDescription', 'asin', 'manufacturer']

with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    for product in data:
        for field in headers:
            if(field not in product):
                product[field]=''
        writer.writerow(product)
print("Extraction Completed!!")
