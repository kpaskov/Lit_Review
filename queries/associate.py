'''
Created on Dec 4, 2012

@author: kpaskov
'''
from model_old_schema.model import get_first
from queries.misc import validate_genes
from queries.move_ref import move_reftemp_to_ref
import json

class Task():
    def __init__(self, task_type, gene_names, comment):
        if task_type == TaskType.ADDITIONAL_LITERATURE: self.ref_curation_name = None; self.topic = 'Additional Literature'
        elif task_type == TaskType.REVIEWS: self.ref_curation_name = None; self.topic = 'Reviews'
        elif task_type == TaskType.HTP_PHENOTYPE_DATA: self.ref_curation_name = 'HTP phenotype'; self.topic = 'Omics'
        elif task_type == TaskType.CLASSICAL_PHENOTYPE_INFORMATION: self.ref_curation_name = 'Classical phenotype information'; self.topic = 'Primary Literature'
        elif task_type == TaskType.DELAY: self.ref_curation_name = 'Delay'; self.topic = 'Primary Literature'
        elif task_type == TaskType.GO_INFORMATION: self.ref_curation_name = 'GO information'; self.topic = 'Primary Literature'
        elif task_type == TaskType.HEADLINE_INFORMATION: self.ref_curation_name = 'Headline information'; self.topic = 'Primary Literature'
        elif task_type == TaskType.HIGH_PRIORITY: self.ref_curation_name = 'High Priority'; self.topic = 'Primary Literature'
        elif task_type == TaskType.OTHER_HTP_DATA: self.ref_curation_name = 'Non-phenotype HTP'; self.topic = 'Omics'
        elif task_type == TaskType.OTHER_PRIMARY_INFORMATION: self.ref_curation_name = None; self.topic = 'Primary Literature'

        self.type = task_type
        self.gene_names = gene_names
        self.comment = comment 
        
class TaskType:
    HIGH_PRIORITY=0
    DELAY=1
    HTP_PHENOTYPE_DATA=2
    OTHER_HTP_DATA=3
    GO_INFORMATION=4
    CLASSICAL_PHENOTYPE_INFORMATION=5
    HEADLINE_INFORMATION=6
    REVIEWS=7
    ADDITIONAL_LITERATURE=8
    OTHER_PRIMARY_INFORMATION=9
    
def get_task_type_by_key(task_key):
        task_type = {'high_priority': TaskType.HIGH_PRIORITY,
                         'delay': TaskType.DELAY,
                         'htp': TaskType.HTP_PHENOTYPE_DATA,
                         'other': TaskType.OTHER_HTP_DATA,
                         'go': TaskType.GO_INFORMATION,
                         'phenotype': TaskType.CLASSICAL_PHENOTYPE_INFORMATION,
                         'headline': TaskType.HEADLINE_INFORMATION,
                         'review': TaskType.REVIEWS,
                         'additional': TaskType.ADDITIONAL_LITERATURE,
                         'primary': TaskType.OTHER_PRIMARY_INFORMATION
                         }[task_key]
        return task_type
    
def task_type_is_gene_specific(task_type):
    gene_specific_tasks = [TaskType.GO_INFORMATION, TaskType.CLASSICAL_PHENOTYPE_INFORMATION, TaskType.HEADLINE_INFORMATION, TaskType.OTHER_PRIMARY_INFORMATION, TaskType.ADDITIONAL_LITERATURE]
    return task_type in gene_specific_tasks
    
def associate(pubmed_id, name_to_feature, tasks, session=None):
    """
    Associate a Reference with LitGuide entries.
    """          
    
    from model_old_schema.reference import Reference, RefCuration, LitGuide
              
    def f(session):
        reference = get_first(Reference, session, pubmed_id=pubmed_id)
   
        for task in tasks:     
            gene_names = task.gene_names
            if gene_names is not None and len(gene_names) > 0:
                #Convert gene_names to features using the name_to_feature table.                
                features = set()
                for gene_name in task.gene_names:
                    features.add(name_to_feature[gene_name.upper()])
                        
                ## Create RefCuration objects and add them to the Reference.
                for feature in features:
                    if task.ref_curation_name is not None:
                        curation = RefCuration.as_unique(session, reference_id=reference.id, task=task.ref_curation_name, feature_id=feature.id)
                        curation.comment = task.comment
                        reference.curations.append(curation)
                                
                ## Create a LitGuide object and attach features to it.
                lit_guide = LitGuide.as_unique(session, topic=task.topic, reference_id=reference.id)
                for feature in features:
                    if not feature.id in lit_guide.feature_ids:
                        lit_guide.features.append(feature)
                reference.litGuides.append(lit_guide)
    
                        
            else:   ## no gene name provided
    
                ## if no gene name provided and "Reviews" was checked,
                ## no need to add any association
                if task.type != TaskType.REVIEWS:
                    curation = RefCuration.as_unique(session, task=task.ref_curation_name, reference_id=reference.id, feature_id=None)
                    curation.comment = task.comment
                    reference.curations.append(curation)
                
                ## Create a LitGuide object.
                if task.type == TaskType.HTP_PHENOTYPE_DATA or task.type == TaskType.OTHER_HTP_DATA or task.type == TaskType.REVIEWS:
                    lit_guide = LitGuide.as_unique(session, topic=task.topic, reference_id=reference.id)
                    reference.litGuides.append(lit_guide)
        return True
    return f if session is None else f(session)

def get_ref_summary(pmid, session=None):
    def f(session):
        from model_old_schema.reference import Reference

        ref = get_first(Reference, session, pubmed_id=pmid)
        curations = ref.curations
        curation_summary = []
        
        for curation in curations:
            if curation.feature is None:
                feature_name = '-'
            elif curation.feature.gene_name is None:
                feature_name = curation.feature.name
            else:
                feature_name = curation.feature.gene_name
            if curation.comment is None:
                comment = '-'
            else:
                comment = curation.comment
            curation_summary.append({'task':curation.task, 'feature':feature_name, 'comment':comment})
        
        litguides = ref.litGuides
        litguide_summary = []
        for litguide in litguides:
            feature_names = []
            for feature in litguide.features:
                if feature.gene_name is None:
                    feature_names.append(feature.name)
                else:
                    feature_names.append(feature.gene_name)
            litguide_summary.append({'topic':litguide.topic, 'features': ', '.join(feature_names)})
            
        ref_summary = {'curations':curation_summary, 'litguides':litguide_summary, 'message':"Reference for pmid = " + pmid + " has been added into the database and associated with the following data:",
                       'curationlink':'http://pastry.stanford.edu/cgi-bin/curation/litGuideCuration?user=' + session.user + '&ref=' + pmid,
                       'sgdlink':'http://pastry.stanford.edu/cgi-bin/reference/reference.pl?dbid=' + ref.dbxref_id}
      
        return json.dumps(ref_summary)  
    return f if session is None else f(session)

#Exceptions

class LinkPaperException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
    
class GeneNamesNotFountException(LinkPaperException):
    def __init__(self, bad_gene_names):
        super(LinkPaperException, self).__init__('The following gene name(s) were not found: ' + ', '.join(bad_gene_names))
        self.bad_gene_names = bad_gene_names
        
class ReferenceNotMovedException(LinkPaperException):
    def __init__(self, pmid):
        super(LinkPaperException, self).__init__("Problem moving temporary reference for pmid = " + pmid + " to the reference table.")
        self.pmid = pmid
        
class AssociateException(LinkPaperException):
    def __init__(self, pmid):
        super(LinkPaperException, self).__init__("An error occurred when linking the reference for pmid = " + pmid + " to the info you entered.")
        self.pmid = pmid
        
class FormNotValidException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
    
class NoGeneNamesException(FormNotValidException):
    def __init__(self, task_key):
        super(FormNotValidException, self).__init__("Please enter gene names for " + task_key)
        self.task_key = task_key

class ReviewCheckedWithoutGenesException(FormNotValidException):
    def __init__(self):
        super(FormNotValidException, self).__init__("If Review is checked with no genes, you cannot check other gene-specific topics.")
        
class GenesWithMultipleTopicsException(FormNotValidException):
    def __init__(self, gene_names):
        super(FormNotValidException, self).__init__("You are trying to assign the following genes to multiple topics: " + ', '.join(gene_names))
     
def check_form_validity_and_convert_to_tasks(data):
    tasks = []
    for key in data.keys(): 
        if key.endswith('_cb'):
            task_key = key[:-3]
            genes_key = task_key + '_genes'
            comment_key = task_key + '_comment'
            
            task_type = get_task_type_by_key(task_key[task_key.find('_')+1:]) 

            if genes_key in data:
                genes = data[genes_key]
                gene_names = genes.replace(',',' ').replace('|',' ').replace(';',' ').replace(':',' ').split()
                
                #Certain tasks must have genes.
                if task_type_is_gene_specific(task_type) and len(gene_names) == 0:
                    raise NoGeneNamesException(task_key)
            else:
                gene_names = [] 
                
            if comment_key in data:
                comment = data[comment_key]
            else:
                comment = '';
                                
            task = Task(task_type, gene_names, comment)   
            tasks.append(task)
    
    #Each gene should be associated with only one topics.
    gene_topic = {}
    genes_with_multiple_topics = []
    for task in tasks:
        for gene in task.gene_names:
            if gene in gene_topic and gene_topic[gene] != task.topic:
                genes_with_multiple_topics.append(gene)
            gene_topic[gene] = task.topic
            
    if len(genes_with_multiple_topics) > 0:
        raise GenesWithMultipleTopicsException(genes_with_multiple_topics)
                  
    
    #If Review is checked without genes, the gene specific tasks should not be checked.
    gene_specific_checked = False
    review_checked_without_genes = False
    for task in tasks:
        if task.type == TaskType.REVIEWS and len(task.gene_names) == 0:
            review_checked_without_genes = True
        if task_type_is_gene_specific(task.type):
            gene_specific_checked = True
    if review_checked_without_genes and gene_specific_checked:
        raise ReviewCheckedWithoutGenesException()
    
    return tasks

def link_paper(pmid, tasks, session=None):
    def f(session):
        all_gene_names = set()
        for task in tasks:
            all_gene_names.update([gene_name.upper() for gene_name in task.gene_names])
    
        name_to_feature = validate_genes(all_gene_names, session)
    
        #If we don't get back as many features as we have gene names, find the bad ones and raise an exception.
        if len(name_to_feature) < len(all_gene_names):
            bad_gene_names = set(all_gene_names) - set(name_to_feature.keys())
            raise GeneNamesNotFountException(bad_gene_names)
    
        #Move reftemp to ref table. Raise an exception if something goes wrong.
        moved = move_reftemp_to_ref(pmid, session)
        if not moved:
            raise ReferenceNotMovedException(pmid)    
    
        #Associate reference with LitGuide and RefCuration objects. Raise an exception if something goes wrong.
        associated = associate(pmid, name_to_feature, tasks, session)
        if not associated:
            raise AssociateException(pmid)
        return True
    
    return f if session is None else f(session)

