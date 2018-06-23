import sys
sys.path.append('systemcalls')
from user import getusers, getuser, getgroups, getshells, updateusershell, getusernotgroups, getusergroups, addusertogroups, removeuserfromgroups
from apps import listinstalled, aptsearch, aptshow, getreponame, addrepo, getexternalrepos
from systemfile import locate,updatedb
from system import getsysteminfo, hostname
from network import ifacestat
from apache import apachestart, apachestop, apacherestart, apachereload, apachestatus, getvhosts, getmods, getconf, activatevhost, deactivatevhost, activatemod, deactivatemod, activateconf, deactivateconf
from apache import apacheconfdir
from cron import listcrontabs
from utilities import readfile, writefile, filedel, filecopy, filerename, mongocheck

from flask import Flask, render_template, flash, request, redirect, url_for, send_file

from flask_bootstrap import Bootstrap

app = Flask(__name__, template_folder = "templates", static_folder = "static", static_url_path = "/static")
app.secret_key = 'random string'
bootstrap = Bootstrap(app)




########## FUNZIONALITÀ user.py ##########

# http://localhost:5000/listUser/
@app.route('/listUserAndGroups')
def listUserAndGroups():
	error = None
	users = getusers()
	groups = getgroups()

	if users['returncode'] != 0 or groups['returncode'] != 0:
		flash("getusers or getgroups fallita")
	else:
		return render_template('users.html', users = users,groups = groups)

	return redirect(url_for('listUserAndGroups'))

# http://localhost:5000/getInfoUser/<clicca valore uname>
@app.route('/getInfoUser/<string:uname>')
def getInfoUser(uname):
	infouser = getuser(uname)
	shells = getshells()
	nogroups = getusernotgroups(uname)
	groupsuser = getusergroups(uname)
	return render_template('info-user.html', infouser = infouser, shells = shells, nogroups = nogroups, groupsuser=groupsuser)

@app.route('/updateShell', methods=['POST'])
def updateShell():
	try:
		error = None
		uname = request.form['unameUpdate'];
		shell = request.form['newShell'];
		if shell == '-- Seleziona nuova shell --':
			flash('Opzione nuova shell non valida')
		else:
			log = updateusershell(uname, shell)
			if(log['returncode'] != 0):
				flash(log['stderr'])
			else:
				flash('Comando shell modificato correttamente')
		
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)

@app.route('/addUserGroup', methods=['POST'])
def addUserGroup():
	try:
		error = None
		uname = request.form['unameAdd'];
		moreGr = request.form['moreGroups'];
		if not uname:
			error = "Errore uname vuoto"
			return render_template("info-user.html",error=error)
		else:
			if not moreGr:
				error = "Errore moreGroups vuoto"
				return render_template("info-user.html",error=error)
			else:
				if moreGr == '-- Seleziona uno o più dei seguenti gruppi --':
					flash('Opzione non valida')
				else:
					log = addusertogroups(uname, moreGr)
					if(log['returncode'] != 0):
						flash(log['stderr'])
					else:
						flash('User aggiunto correttamente al/i gruppo/i')
		
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)

@app.route('/removeUserGroup', methods=['POST'])
def removeUserGroup():
	try:
		error = None
		uname = request.form['unameRem'];
		moreGr = request.form['moreGroups'];
		if not uname:
			error = "Errore uname vuoto"
			return render_template("info-user.html",error=error)
		else:
			if not moreGr:
				error = "Errore moreGroups vuoto"
				return render_template("info-user.html",error=error)
			else:
				if moreGr == '-- Seleziona uno o più dei seguenti gruppi --':
					flash('Opzione non valida')
				else:
					log = removeuserfromgroups(uname, moreGr)
					if(log['returncode'] != 0):
						flash(log['stderr'])
					else:
						flash('User eliminato correttamente dal/i gruppo/i')
		
		return redirect(url_for('listUserAndGroups'))
	except Exception:
		return internal_server_error(500)




########## FUNZIONALITÀ cron.py ##########

@app.route('/listCron')
def listCron():
	listCrontabs = listcrontabs()
	return render_template("jobs.html",listCrontabs=listCrontabs)

@app.route('/getContentCrontab/<string:cronk>/<string:cronv>')
def getContentCrontab(cronk,cronv):
	basedir='/etc/'
	pathCron=basedir+cronk+'/'+cronv
	content = readfile(pathCron)
	#return send_file(pathCron,attachment_filename=cronv) fa il download
	return render_template("jobs-details.html", content=content, pathCron=pathCron)

@app.route('/updateCrontab', methods=['POST'])
def updateCrontab():
	try:
		error = None
		updatedCrontab = request.form['contentTextarea']
		path = request.form['hiddenPath']
		if not updateCrontab and not path:
			error = "Errore passaggio parametri: vuoti"
			return render_template("jobs.html", error=error)
		else:
			newPath = writefile(path, updatedCrontab)
			if(newPath['returncode'] != 0):
				error = "Modifica cron fallita"
				return render_template("jobs.html", error=error)
			else:
				flash("Modifica avvenuta correttamente")
				return redirect(url_for('listCron'))
	except Exception:
		return internal_server_error(500)	



########## FUNZIONALITÀ apps.py ##########

# http://localhost:5000/listInstalled
@app.route('/listInstalled')
def listInstalled():
	listAppInst = listinstalled(True)
	generatedRepoName = getreponame()
	return render_template('applications.html', listAppInst = listAppInst, generatedRepoName=generatedRepoName)

@app.route('/findPkgInstalled', methods=['POST'])
def findPkgInstalled():
	error = None
	pkg = request.form['pkgSearch'];
	if not pkg:
		flash(u'Operazione errata, impossibile ricercare stringa vuota','warning')
		return redirect(url_for('listInstalled'))
	else:	
		appFound = aptsearch(pkg)
		return render_template('find-pkg-installed.html', appFound = appFound)

@app.route('/getInfoApp/<string:name>')
def getInfoApp(name):
	infoApp = aptshow(name)['data']
	infoApp = infoApp.replace('\n', '<br>')
	return render_template('info-app.html', infoApp = infoApp, name = name)

@app.route('/addRepo', methods=['POST'])
def addRepo():
	error = None
	contentRepo = request.form['contentTextarea']
	repoName = request.form['nameRepo']
	log = addrepo(contentRepo,repoName)
	if log['returncode'] != 0:
		error = 'Errore nell\'aggiunta del repository'
		return render_template('applications.html',error=error)
	else:
		flash(u'Repository aggiunto con successo!','success')
		return redirect(url_for('listInstalled'))

@app.route('/removeRepo')
def removeRepo():
	pass

@app.route('/aggiornaCachePacchetti')
def aggiornaCachePacchetti():
	pass

@app.route('/retrieveExternalRepo')
def retrieveExternalRepo():
	listOtherRepo = getexternalrepos()['data']
	return render_template("other-repo.html", listOtherRepo=listOtherRepo)

########## FUNZIONALITÀ systemfile.py ##########

@app.route('/file')
def file():
	return render_template('file.html')

@app.route('/findFile', methods=['POST'])
def findFile():
	error = None
	fs = request.form['fileSearch'];
	if not fs:
		flash(u'Impossibile cercare stringa vuota','error')
	else:
		pathFileFound = locate(fs);
		if not pathFileFound:
			error = "Nessun file trovato"
			return render_template('file.html',error=error)
		else:
			return render_template('file.html', pathFileFound = pathFileFound)
		
	return redirect(url_for('file'))

@app.route('/updateDbFile', methods=['POST'])
def updateDbFile():
	try:
		error = None
		if request.form['updateDbFile'] == 'Aggiorna DB File':
			log = updatedb()
			if(log['returncode'] != 0):
				error = 'Database dei file non aggiornato'
				return render_template('file.html',error=error)
			else:
				flash(u'Aggiornato!','info')
				return redirect(url_for('file'))
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/retriveContentFile', methods=['POST'])
def retriveContentFile():
	try:
		error = None
		if request.form['retriveContentFile'] == 'Modifica':
			pathFile = request.form['pathFile']
			if not pathFile:
				error = "Path vuoto"
				return render_template("file.html",error=error)
			else:
				fileContent = readfile(pathFile)
				if(fileContent['returncode'] != 0):
					error = fileContent['command']
				else:
					return render_template("file-content.html", fileContent=fileContent, pathFile=pathFile)
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/updateFile', methods=['POST'])
def updateFile():
	try:
		error = None
		pathFile = request.form['pathFile']
		updatedContentFile = request.form['contentTextarea']
		newContent = writefile(pathFile,updatedContentFile)
		if(newContent['returncode'] != 0):
			error = "Errore in fase di modifica"
			return render_template("file.html",error=error)
		else:
			flash(u'Modifica avvenuta correttamente!','info')
			return redirect(url_for('file'))
	except Exception:
		return internal_server_error(500)

@app.route('/deleteFile', methods=['POST'])
def deleteFile():
	try:
		error = None
		if request.form['deleteFile'] == 'Elimina':
			pathFile = request.form['pathFile']
			if not pathFile:
				error = "Path vuoto"
				return render_template("file.html",error=error)
			else:
				log = filedel(pathFile)
				if(log['returncode'] != 0):
					error = log['stderr']
					return render_template('file.html',error=error)
				else:
					log = updatedb()
					if(log['returncode'] != 0):
						error = 'Database dei file non aggiornato'
						return render_template('file.html',error=error)
					else:
						flash(u'File eliminato correttamente!','info')
						return redirect(url_for('file'))
		else:
			error = 'Non funzica' 
		return render_template('file.html', error=error)
	except Exception:
		return internal_server_error(500)


@app.route('/copyFile', methods=['POST'])
def copyFile():
	error = None
	if request.form['copyFile'] == 'Copia':
		pathFile = request.form['pathFile']
		pathDest = request.form['destPathFile']
		if not pathFile:
			error = "Path vuoto"
			return render_template("file.html",error=error)
		elif not pathDest:
			error = "Path destinazione non può essere vuoto"
			return render_template("file.html",error=error)
		else:
			log = filecopy(pathFile,pathDest)
			if(log['returncode'] != 0):
				error =	log['stderr']
				return render_template("file.html",error=error)
			else:
				log = updatedb()
				if(log['returncode'] != 0):
					error = 'Database dei file non aggiornato'
					return render_template('file.html',error=error)
				else:
					flash(u'File copiato correttamente!','info')
					return redirect(url_for('file'))
	else:
		error = 'Non funzica'	

@app.route('/renameFile', methods=['POST'])
def renameFile():
	error = None
	if request.form['renameFile'] == 'Rinomina':
		pathFile = request.form['pathFile']
		newName = request.form['newNameFile']
		if not pathFile:
			error = "Path vuoto"
			return render_template("file.html",error=error)
		elif not newName:
			error = "Nessun nuovo nome inserito"
			return render_template("file.html",error=error)
		else:
			log = filerename(pathFile,newName)
			if(log['returncode'] != 0):
				error =	log['stderr']
				return render_template("file.html",error=error)
			else:
				log = updatedb()
				if(log['returncode'] != 0):
					error = 'Database dei file non aggiornato'
					return render_template('file.html',error=error)
				else:
					flash(u'File rinominato correttamente!','info')
					return redirect(url_for('file'))
	else:
		error = 'Non funzica'

########## FUNZIONALITÀ system.py ##########
#http://localhost:5000/dash
# definizione base dash con componente fissa navbar
@app.route('/dash')
def dash():
	tpl = getsysteminfo()
	(cpu,mem,proc) = tpl['data']
	return render_template('dash.html', cpu = cpu, mem = mem, proc = proc)

@app.route('/param')
def param():
	error = None
	hname = hostname()
	if(hname['returncode'] != 0):
		flash(hname['stderr'])
	else:
		return render_template('param.html', hname=hname)
	return render_template('param.html')

@app.route('/newHostname', methods=['POST'])
def newHostname():
	try:
		error = None
		hname = request.form['newHname'];
		if not hname:
			flash('Hostname non può essere vuoto!')
		else:
			log = hostname(hname)
			if(log['returncode'] != 0):
				flash(log['stderr'])
			else:
				flash('Hostname modificato correttamente')
		
		return redirect(url_for('param'))
	except Exception:
		return internal_server_error(500)



'''questa logica non va bene'''
########## FUNZIONALITÀ network.py ##########
@app.route('/network')
def network():
	key_remove = list()
	lo = dict()
	als = dict()
	facestat = ifacestat()['data']
	for key,value in facestat.items():
		if 'LOOPBACK' in value[-1]:
			lo.update({key:facestat[key]})
			key_remove.append(key)
		elif ':' in key:
			als.update({key:facestat[key]})
			key_remove.append(key)
	for key in key_remove:
		del facestat[key]
	return render_template('network.html', facestat=facestat,lo=lo, als=als)





########## FUNZIONALITÀ apache.py ##########

@app.route('/startApache', methods=['POST'])
def startApache():
	try:
		error = None
		if request.form['b-start-a'] == 'Start':
			log = apachestart()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache startato correttamente")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

#errore 500
@app.route('/stopApache', methods=['POST'])
def stopApache():
	try:
		error = None
		if request.form['b-stop-a'] == 'Stop':
			log = apachestop()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Apache stoppato correttamente")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

# return HTTP/1.1" 302
@app.route('/restartApache', methods=['POST'])
def restartApache():
	try:
		error = None
		if request.form['b-restart-a'] == 'Restart':
			log = apacherestart()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Restart Apache avvenuto correttamente")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/reloadApache', methods=['POST'])
def reloadApache():
	try:
		error = None
		if request.form['b-reload-a'] == 'Reload':
			log = apachereload()
			if(log['returncode'] != 0):
				error = log['stderr']
			else:
				flash("Reload Apache avvenuto correttamente")
				return redirect(url_for('sites'))
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/statusApache', methods=['POST'])
def statusApache():
	try:
		error = None
		if request.form['b-status-a'] == 'Status':
			logStatus = apachestatus()
			if(logStatus['returncode'] != 0):
				error = logStatus['stderr']
			else:
				return render_template('apache-sites.html', logStatus=logStatus)
		else:
			error = 'Non funzica' 
		return render_template('apache-sites.html', error=error)
	except Exception:
		return internal_server_error(500)

@app.route('/sites')
def sites():
	error=None
	vhost=getvhosts()
	if(vhost['returncode'] != 0):
		flash(vhost['stderr'])
		return redirect(url_for('sites'))
	else:
		return render_template('apache-sites.html', vhost=vhost)

@app.route('/retrieveContentSite', methods=['POST'])
def retrieveContentSite():
	nameSite = request.form['retrieveCS']
	contentVhost = readfile(apacheconfdir+"sites-available/"+nameSite)
	return render_template('apache-site-content.html', contentVhost=contentVhost, nameSite=nameSite)

@app.route('/updateContentSite/<string:nameSite>', methods=['POST'])
def updateContentSite(nameSite):
	try:
		error = None
		updatedContentVhost = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"sites-available/"+nameSite,updatedContentVhost)
		if(newContent['returncode'] != 0):
			error = "Errore in fase di modifica"
			return render_template('apache-sites.html',error=error)
		else:
			flash("Modifica avvenuta correttamente")
			return redirect(url_for('sites'))
	except Exception:
		return internal_server_error(500)

@app.route('/modules')
def modules():
	error=None
	mods=getmods()
	if(mods['returncode'] != 0):
		flash(mods['stderr'])
		return redirect(url_for('sites'))
	else:
		return render_template('apache-modules.html', mods=mods)

@app.route('/retrieveContentModule', methods=['POST'])
def retrieveContentModule():
	nameMods = request.form['retrieveCM']
	contentMods = readfile(apacheconfdir+"mods-available/"+nameMods)
	return render_template('apache-module-content.html', contentMods=contentMods, nameMods=nameMods)

@app.route('/updateContentMods/<string:nameMods>', methods=['POST'])
def updateContentMods(nameMods):
	try:
		error = None
		updatedContentMods = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"mods-available/"+nameMods,updatedContentMods)
		if(newContent['returncode'] != 0):
			error = "Errore in fase di modifica"
			return render_template('apache-modules.html',error=error)
		else:
			flash("Modifica avvenuta correttamente")
			return redirect(url_for('modules'))
	except Exception:
		return internal_server_error(500) 

@app.route('/configurations')
def configurations():
	error=None
	conf=getconf()
	if(conf['returncode'] != 0):
		flash(conf['stderr'])
		return redirect(url_for('sites'))
	else:
		return render_template('apache-configurations.html', conf=conf)

@app.route('/retrieveContentConfiguration', methods=['POST'])
def retrieveContentConfiguration():
	nameConf = request.form['retrieveCC']
	contentConf = readfile(apacheconfdir+"conf-available/"+nameConf)
	return render_template('apache-configuration-content.html', contentConf=contentConf, nameConf=nameConf)

@app.route('/updateContentConf/<string:nameConf>', methods=['POST'])
def updateContentConf(nameConf):
	try:
		error = None
		updatedContentConf = request.form['contentTextarea']
		newContent = writefile(apacheconfdir+"conf-available/"+nameConf,updatedContentConf)
		if(newContent['returncode'] != 0):
			error = "Errore in fase di modifica"
			return render_template('apache-configurations.html',error=error)
		else:
			flash("Modifica avvenuta correttamente")
			return redirect(url_for('configurations'))
	except Exception:
		return internal_server_error(500) 

#creating a view function without returning a response in Flask
# return HTTP/1.1" 204
@app.route('/activateVHost', methods=['POST'])
def activateVHost():
	filename = request.form['clickActiv']
	if filename:
		logAVHost=activatevhost(filename)
		if(logAVHost['returncode'] != 0):
			flash(logAVHost['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateVHost', methods=['POST'])
def deactivateVHost():
	filename = request.form['clickDeactiv']
	if filename:
		logDAVHost=deactivatevhost(filename)
		if(logDAVHost['returncode'] != 0):
			flash(logDAVHost['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/activateMods', methods=['POST'])
def activateMods():
	filename = request.form['clickActiv']
	if filename:
		logAMod=activatemod(filename)
		if(logAMod['returncode'] != 0):
			flash(logAMod['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateMods', methods=['POST'])
def deactivateMods():
	filename = request.form['clickDeactiv']
	if filename:
		logDAMod=deactivatemod(filename)
		if(logDAMod['returncode'] != 0):
			flash(logDAMod['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/activateConf', methods=['POST'])
def activateConf():
	filename = request.form['clickActiv']
	if filename:
		logAConf=activateconf(filename)
		if(logAConf['returncode'] != 0):
			flash(logAConf['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask

@app.route('/deactivateConf', methods=['POST'])
def deactivateConf():
	filename = request.form['clickDeactiv']
	if filename:
		logDAConf=deactivateconf(filename)
		if(logDAConf['returncode'] != 0):
			flash(logDAConf['stderr'])
			#return redirect(url_for('sites'))
			return '',204
	#return redirect(url_for('sites'))
	return '',204 #ritorno senza reindirizzamento con flask


########### CHECK MONGODB ###########
@app.before_request
def before_request():
	log = mongocheck()
	if(log['returncode'] == 42):
		error = log['stderr']
		return render_template('mongo.html',error=error)


########## GESTIONE ERRORI ##########
 
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
	app.run(debug = True)
