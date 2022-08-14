## FUNCTIONS
def getRawHTML(link):
    
    r = get(link, headers={'User-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'})
    c = r.content
    soup = BeautifulSoup(c, "html.parser")
    
    return soup

def retrieveServiceData(data):
    
    all = data.find_all('table', {"class": "typetable"})
    
    serviceArr = []
    for item in all[0].find_all('tr'):
        serviceObj = {}
        
        try:
            service = item.find_all('td')[0].find('a', {"class": "link"}).text
            serviceObj['service'] = service
        except:
            service = 'NA'
        
        try:
            desc = item.find_all('td')[1].text.replace("\n", "")
            serviceObj['description'] = desc
        except:
            desc = 'NA'
        
        try:
            postStr = item.find('a', {"class": 'link'})['href']
            link = base_url + postStr
            serviceObj['link'] = link
        except:
            link = 'NA'
    
        if serviceObj:
            serviceArr.append(serviceObj)
    
    fileDir = dirPath +'/service'
    if not path.exists(fileDir):
        mkdir(fileDir)
        
    with open(path.join(fileDir, '') + 'service.json', 'w+') as outfile:
        dump(serviceArr, outfile)
        
    return serviceArr

def retrieveOperationData(data, index):
    
    all = data.find_all('table', {"class": "typetable"})

    operationArr = []
    for item in all[0].find_all('tr'):
        operationOj = {}
        
        try:
            ops = item.find_all('td')[0].find('a', {"class": "link"}).text
            operationOj['operation'] = ops
        except:
            ops = 'NA'
        
        try:
            desc = item.find_all('td')[1].text.replace("\n", "").replace("\u00a0", "")
            operationOj['description'] = desc
        except:
            desc = 'NA'
        
        try:
            postStr = item.find('a', {"class": 'link'})['href']
            link = base_url + serviceArr[index]['service'] + '/v38.2/' + postStr
            link = link.strip()
            operationOj['link'] = link
        except:
            link = 'NA'
    
        if operationOj:
            operationOj['service'] = serviceArr[index]['service']
            operationArr.append(operationOj)
    
    fileDir = dirPath +'/operation'
    if not path.exists(fileDir):
        mkdir(fileDir)
        
    individual_ops_target_dir = fileDir + '/'+ serviceArr[index]['service'] +'/'
    if not path.exists(individual_ops_target_dir):
        mkdir(individual_ops_target_dir)
    
    with open(path.join(individual_ops_target_dir, '') + serviceArr[index]['service'] + '.json', 'w+') as outfile:
        dump(operationArr, outfile)
    
    return operationArr

def retrieve(hrefName, data):
    fieldsArr = []
    for i in data:
        for j in i.find_all('td'):
            if j.find('a', {"name": hrefName}):
                fieldsData = (j.find('table', {"class": 'typetable'})).find_all('tr')
                for item in fieldsData:
                    if len(item.find_all('td')) > 2:
                        fieldsObj = {}
                        try:
                            fieldsObj['parameterName'] = item.find_all('td')[0].text.replace("\n", "").replace("\xa0", "")
                        except:
                            fieldsObj['parameterName'] = 'NA'

                        try:
                            fieldsObj['type'] = item.find_all('td')[1].text.replace("\n", "").replace("\xa0", "")
                            if ((item.find_all('td')[1]).find('a')):
                                if ((item.find_all('td')[1]).find('a')).get('href'): 
                                    fieldsObj[item.find_all('td')[1].text.replace("\n", "").replace("\xa0", "")] = retrieve(((item.find_all('td')[1]).find('a')).get('href')[1:], data)
                        except:
                            fieldsObj['type'] = 'NA'
                            
                        try:
                            fieldsObj['cardinality'] = item.find_all('td')[2].text.replace("\n", "").replace("\xa0", "")
                        except:
                            fieldsObj['cardinality'] = 'NA'
    
                        try:
                            fieldsObj['description'] = item.find_all('td')[3].text.replace("\n", "").replace("\xa0", "")
                        except:
                            fieldsObj['description'] = 'NA'
                            
                        if fieldsObj:
                            fieldsArr.append(fieldsObj)
        
    return fieldsArr

def retrieveFieldData(link, service, operation):
    
    rawFieldData = getRawHTML(link)    
    ulList = rawFieldData.find_all('ul')[2]
    requesthreflink = ((ulList.find('li')).find('a'))['href'][1:]
    data = rawFieldData.find_all('table')[0].find_all('tr')
    xyz = retrieve(requesthreflink, data)

    if service:
        fileDir = dirPath +'/operation/' + service + '/fields'
        if not path.exists(fileDir):
            mkdir(fileDir)
        
        if operation:
            with open(path.join(fileDir, '') + operation + ".json", "w+") as outfile:
                dump(xyz, outfile)
        else:
            print("NOT OPERATION")
    else:
        print("NOT SERVICE")
    
        
    return True


from requests import get
from json import dump
from os import getcwd
from os import path
from os import mkdir
from tqdm import tqdm
from bs4 import BeautifulSoup
from multiprocessing import Pool, Process
import threading

dirPath = getcwd()

base_url = "https://community.workday.com/sites/default/files/file-hosting/productionapi/"

## Service Extraction
rawServiceData = getRawHTML("https://community.workday.com/sites/default/files/file-hosting/productionapi/index.html")
serviceArr = retrieveServiceData(rawServiceData)
pool=Pool(processes=5)
process = []
threads = []
## Operations Extraction
for index in tqdm(range(len(serviceArr))):
    rawOperationData = getRawHTML(serviceArr[index]['link'].strip())
    operationArr = retrieveOperationData(rawOperationData, index)
    
    ## Fields of Operation Extraction
    for id in range(len(operationArr)):
        #pool.apply_async(retrieveFieldData,(operationArr[id]['link'].strip(), operationArr[id]['service'], operationArr[id]['operation'],))
        #t = threading.Thread(target=retrieveFieldData, args=(operationArr[id]['link'].strip(), operationArr[id]['service'], operationArr[id]['operation'],))
        #threads.append(t)
        #t.start()
        p=Process(target=retrieveFieldData,args=(operationArr[id]['link'].strip(), operationArr[id]['service'], operationArr[id]['operation'],))
        process.append(p)
        #p.start()
    
step_size = 10    
initial = 0
x = range(initial, len(process)-1000, step_size)
for p in tqdm(range(initial, len(process)-1000, step_size)):
    #print(range(step_size))
    for step in range(initial, step_size):
        #print(process[step])
        process[step].start()
    
    initial = step_size
    step_size = step_size + 10
    process[p].join()


print ("Done")
