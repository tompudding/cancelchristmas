while True:
  print 'Welcome to Market Research. Enter your UID:'
  uid = raw_input()
  with con:
    cur = con.cursor()
    try:
      #Mrs Claus keeps insisting that this is vulnerable to an 
      #SQL injection attack. Nag Nag Nag.
      command = "SELECT Name,Password from Passwords WHERE UID = '%s'" % uid
      results = database.execute(command)
    except error as e:
      print 'Error with UID',str(e)
    if results == None:
      print 'No such UID'

    name,password = results[0]
    print 'Greetings %s, what is your password?' % (name)
    given_password = raw_input()
    if given_password == password:
      print 'Access granted'
      door.toggle()
    else:
      print 'Access denied'
