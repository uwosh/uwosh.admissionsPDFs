from DateTime import DateTime
def clearExpiredPDFs(self):
    delObjs = []
    ##for folders in self... check if expired... if expired delete them and their children
    for obj in self.objectValues():
	if obj.meta_type == "ATFolder":
	    if hasattr(obj, 'expiration_date'):
	        if obj.expiration_date < DateTime():
		    if obj.wl_isLocked():
    			obj.wl_clearLocks()
		    self.manage_delObjects(ids=[str(obj.id)])
		    delObjs.append(obj.id)    	
    self.REQUEST.RESPONSE.redirect(self.absolute_url())
    return delObjs
