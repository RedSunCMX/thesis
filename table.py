import os

counter=0
newList=[]
directory = "log\\descMatch\\"
files = os.listdir(directory)
for x in range(len(files)):
    file = open(directory + str(files[x]))
    html = open('log\\descMatch\\descMatch.html','w')
    html.write('<table border="1">')
    for line in file:
        cell = line.split('";"')
        html.write('<td>' + cell[0]),
        newList=[]
        for i in range(1,len(cell)):
            counter += 1
            newList.append('<td>' + cell[i] + '</td>')
            if counter == 3:
                tr = '<tr>' + ' '.join(newList[:2]) + '</tr>'
                newList=[]
                html.write(tr)
                counter = 0
        html.write('</td>')
    html.write('</table>')
    html.close()
    os.rename('log\\descMatch\\descMatch.html',directory + str(files[x]) + ".html")
