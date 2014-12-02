##Uses a PFG form to select and merge various PDFs to create a custom viewbook for prospective students
##The PFG form should send a unique username and up to 6 majors and/or areas of interests in the query string
from pyPdf import PdfFileWriter, PdfFileReader
from Products.CMFPlone.utils import _createObjectByType
import os.path
import random
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
import StringIO

folderPermissionsList = ['ATContentTypes: Add File', 'ATContentTypes: Add Document', 'Access session data', 'ATContentTypes: Upload via url', 'Add portal content', 'Modify portal content', 'ATContentTypes: Add Folder', 'List folder contents', 'Access contents information']##Access contents information

pageText = """
    <h2>Hello, %s</h2>

    <p>Welcome to your custom UW Oshkosh web site. Contained in this site is a custom viewbook created based on your areas of interest.
    Also below are links to more information on the areas of interest that you have selected.</p>

    <p>Your custom viewbook is located here: <a href=%s>%s</a></p>

    <h4>%s's Links:</h4>
    <ul>%s</ul>

    <p>Please copy this page's URL if you wish to visit it again in the future. This page will live for 14 days unless you choose to extend
    it's life. At the end of it's life it will be deleted but you are free to create another custom site and viewbook as you wish.</p>
    """

def addPath(self, pdf):
    try:
        aPDF = self['source-pdfs']['%s' % (pdf)]
        thePDF = StringIO.StringIO(aPDF)

    except:
        return "PDF not found"

    return thePDF 

def addTempPath(pdf):
    pathToPdfs = "/tmp/"##a place to create pdfs on the filesystem temporarily should be /tmp when upload this
    pdfPlusPath = pathToPdfs + pdf
    return pdfPlusPath

def changePermissions(obj, pList=[], roles=[]):
    for p in pList:
        obj.manage_permission(p, roles)

def reduceList(pdfs):
    """
    Gets unique pdf values and alphabetize them
    """
    uniq = set(pdfs)
    return [pdf for pdf in pdfs if pdf in uniq and not uniq.remove(pdf)]
    
def createViewbook(self, username, pdf1, pdf2, pdf3, pdf4, pdf5, pdf6):
    portal_workflow = getToolByName(self, 'portal_workflow')
    pdfList = [pdf1, pdf2, pdf3, pdf4, pdf5, pdf6]
    pdfs = reduceList(pdfList)
    
    ##Retrieve pdf cover and end page
    coverPdf = PdfFileReader(addPath(self, 'coverpage.pdf'))
    coverPage = coverPdf.getPage(0)
    endPdf = PdfFileReader(addPath(self, 'guideline.pdf'))
    endPage = endPdf.getPage(0)

    ##Open a pdf file writer, write cover page, selected pdfs, and end page
    output = PdfFileWriter()
    output.addPage(coverPage)
    for i, pdf in enumerate(pdfs):
   	if pdf in self['source-pdfs'].objectIds():
	    thisPdf = PdfFileReader(addPath(self, pdf))
            numPages = thisPdf.getNumPages()
            for i in range(numPages):
                pageInPdf = thisPdf.getPage(i)
                output.addPage(pageInPdf)
        else:
            pass

    ####create and set pdf and page variables
    usernameX = username.replace("_", " ")
    studentViewBook = "%s-viewbook.pdf" % (username.replace(" ", "_"))
    customPageName = "%s's Custom Webpage" % (usernameX)
    svbTitle = "%s's Custom Viewbook" % (usernameX)
    output.addPage(endPage)
    outputStream = file(addTempPath(studentViewBook), "wb")
    output.write(outputStream)
    outputStream.close()
    fileToAdd = file(addTempPath(studentViewBook), "rb")

    ##create a unique id for the folder and page check for existance of objects with the same uid
    while True:
        uniqueFolderId = random.randrange(100000000000, 999999999999)
        if uniqueFolderId not in self.objectIds():
            break
    while True:
        uniquePageId = random.randrange(100000000000, 999999999999)
        if uniquePageId not in self.objectIds():
            break

    ##create folder to hold page and pdf and set permissions
    self.invokeFactory(type_name="Folder", id=uniqueFolderId)##treating this as  long integer and not just folder
    viewbookFolder = self[str(uniqueFolderId)]
    changePermissions(viewbookFolder, folderPermissionsList, roles=['Anonymous', 'Manager'])
    viewbookFolder.manage_permission('View', roles=['Anonymous', 'Manager'], acquire=0)     
    viewbookFolder.invokeFactory(type_name="File", id=studentViewBook, file=fileToAdd, title=svbTitle, format='application/pdf')
    viewbookFolder[str(studentViewBook)].manage_permission('View', roles=['Anonymous', 'Manager'], acquire=0)
    viewbookFolder.setExcludeFromNav(True)
    viewbookFolder.setExpirationDate(DateTime() + 14)
    viewbookFolder.reindexObject()
    viewbook_url = viewbookFolder.absolute_url() + "/" + str(studentViewBook)
    
    ##generate links for each area of interest selected
    linksHtml = "" 
    for pdf in pdfs:
        if pdf != "---":
            linksHtml = linksHtml + "<li><a href='%s'>%s</a></li> \n" % (self[str(uniqueFolderId)].absolute_url() + "/" + str(pdf), pdf)
    
    ##set bodyText of page
    bodyText = pageText % (usernameX, viewbook_url, viewbook_url, usernameX, linksHtml)

    ##create custom web page
    viewbookFolder.invokeFactory(type_name="Document", id=uniquePageId, title=customPageName, text_format='html', text=bodyText)
    viewbookFolder.setDefaultPage(str(uniquePageId))
    viewbookFolder[str(uniquePageId)].manage_permission('View', roles=['Anonymous', 'Manager'], acquire=0)
    viewbookFolder[str(uniquePageId)].manage_permission('Access contents information', roles=['Manager'], acquire=0)
    self.portal_workflow.doActionFor(viewbookFolder, 'publish')
    self.portal_workflow.doActionFor(viewbookFolder[str(uniquePageId)], 'publish')

    ##refresh the page
    self.REQUEST.RESPONSE.redirect(viewbookFolder.reference_url())
    
    ##remove the pdf from the file system after uploaded to Plone
    if os.path.exists(addTempPath(studentViewBook)):
        os.remove(addTempPath(studentViewBook))

    ##remove permissions from anonymous
    changePermissions(viewbookFolder, folderPermissionsList, roles=['Manager'])






    
