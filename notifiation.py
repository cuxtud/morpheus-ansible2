import mysql.connector
from mysql.connector import Error
try:
   mySQLconnection = mysql.connector.connect(host='127.0.0.1',
                             database='morpheus',
                             user='morpheus',
                             password='c7ad41c0538d286680a79762')

   sql_select_Query = "SELECT req.request_by AS 'Requested By', u.email AS 'Requested By Email', rf.ref_id AS 'Instance ID', rf.approved_by AS 'Approved By', rf.date_created AS 'Date Created', rf.date_approved AS 'Date Approved', rf.denied_by AS 'Denied By', rf.date_denied AS 'Date Denied', rf.status AS 'Status', ins.name AS 'Instance Name', acc.id AS 'Tenant ID', acc.name AS 'Tenant Name', ins.expire_days AS 'Expires Days', ins.max_cores AS 'Cores', ins.max_memory AS 'Memory', ins.max_storage AS 'Storage', ins_t.name AS 'Instance Type Name', plan.name AS 'Plan Name' FROM request_reference AS rf INNER JOIN request AS req ON req.id = rf.request_id INNER JOIN user AS u on u.id = req.request_by_user_id INNER JOIN instance AS ins ON ins.id = rf.ref_id INNER JOIN account AS acc ON acc.id = ins.account_id INNER JOIN instance_type AS ins_t ON ins_t.id = ins.instance_type_id INNER JOIN service_plan AS plan on plan.id = ins.plan_id;"
   cursor = mySQLconnection .cursor()
   cursor.execute(sql_select_Query)
   records = cursor.fetchall()

   print("Total number approvals is - ", cursor.rowcount)
   print ("Printing each row's column values i.e.  Approval requests")
   for row in records:
       print("Requestor Name = ", row[0], )
       print("Email = ", row[1])
       print("Instance ID  = ", row[2])
       print("Approved by  = ", row[3])
       print("Date Created  = ", row[4])
       print("Date Approved  = ", row[5])
       print("Denied by  = ", row[6])
       print("Date Denied = ", row[7])
       print("Status = ", row[8])
       print("Instance Name = ", row[9])
       print("Tenant ID = ", row[10])
       print("Tenant Name = ", row[11])
       print("Expires Days = ", row[12])
       print("Cores = ", row[13])
       print("Memory = ", row[14])
       print("Storage = ", row[15])
       print("Instance Type Name = ", row[16])
       print("Plan Name = ", row[17], "\n")

   cursor.close()
   
except Error as e :
    print ("Error while connecting to MySQL", e)
finally:
    #closing database connection.
    if(mySQLconnection .is_connected()):
        connection.close()
        print("MySQL connection is closed")