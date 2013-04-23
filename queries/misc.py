'''
Created on Dec 4, 2012

@author: kpaskov
'''
from model_old_schema.model import get_first, get
from sqlalchemy.sql.expression import func
from webapp.litreview_logger import log_it
import datetime
import string

    
def get_reftemps(session=None):
    
    from model_old_schema.reference import RefTemp

    def f(session):
        return get(RefTemp, session)
    
    return f if session is None else f(session)

def validate_genes(gene_names, session=None):
    """
    Convert a list of gene_names to a mapping between those gene_names and features.
    """            
    
    from model_old_schema.feature import Feature, Alias

    def f(session):
        if gene_names is not None and len(gene_names) > 0:
            upper_gene_names = [x.upper() for x in gene_names]
            fs_by_name = set(session.query(Feature).filter(func.upper(Feature.name).in_(upper_gene_names)).filter(Feature.type != 'chromosome').all())
            fs_by_gene_name = set(session.query(Feature).filter(func.upper(Feature.gene_name).in_(upper_gene_names)).filter(Feature.type != 'chromosome').all())
            
            log_it('DB_query', 'SUCCESS')
            all_names_left = set(upper_gene_names)
      
            #Create table mapping name -> Feature        
            name_to_feature = {}
            for f in fs_by_name:
                name_to_feature[f.name.upper()] = f
            for f in fs_by_gene_name:
                name_to_feature[f.gene_name.upper()] = f
    
            all_names_left.difference_update(name_to_feature.keys())
            
            if len(all_names_left) > 0:
                aliases = session.query(Alias).filter(func.upper(Alias.name).in_(all_names_left)).all()
            else:
                aliases = []
            log_it('Create table mapping feature', 'SUCCESS')

            #Create table mapping name -> Alias
            name_to_alias = {}
            for a in aliases:
                features = [f for f in a.features if f.type != 'chromosome']
                if len(features) > 0:
                    if a.name in name_to_alias:
                        name_to_alias[a.name.upper()].update(features)
                    else:
                        name_to_alias[a.name.upper()] = set(features)
            log_it('Create table mapping alias', 'SUCCESS')
                        
            #This may be a gene name with p appended
            p_endings = [word[:-1] for word in all_names_left if word.endswith('P')]
            p_ending_fs_by_name = set()
            p_ending_fs_by_gene_name = set()
            if len(p_endings) > 0:
                p_ending_fs_by_name.update(session.query(Feature).filter(func.upper(Feature.name).in_(p_endings)).filter(Feature.type != 'chromosome').all())
                p_ending_fs_by_gene_name.update(session.query(Feature).filter(func.upper(Feature.gene_name).in_(p_endings)).filter(Feature.type != 'chromosome').all())
            
            all_names_left.difference_update(name_to_alias.keys())
            log_it('p appended', 'SUCCESS')
             
            #Add to Alias table all p-ending gene names
            for p_ending in p_ending_fs_by_name:
                word = p_ending.name + 'P'
                if word in name_to_alias:
                    name_to_alias[word.upper()].add(p_ending)
                else:
                    name_to_alias[word.upper()] = set([p_ending])
                    
            for p_ending in p_ending_fs_by_gene_name:
                word = p_ending.gene_name + 'P'
                if word in name_to_alias:
                    name_to_alias[word.upper()].add(p_ending)
                else:
                    name_to_alias[word.upper()] = set([p_ending])
            log_it('Add to alias table', 'SUCCESS')
                               
            alias_message = create_alias_message(name_to_alias)
            feature_message = create_feature_message(name_to_feature)
            not_genes_message = create_not_genes_message(all_names_left)
            log_it('Create messages', 'SUCCESS')
               
            return {'features':name_to_feature, 'aliases':name_to_alias, 'not_genes':all_names_left, 'alias_message':alias_message, 'feature_message':feature_message, 'not_genes_message':not_genes_message}
        else:
            return {'features':{}, 'aliases':{}, 'not_genes':set(), 'alias_message':'', 'feature_message':'', 'not_genes_message':''}
        
    return f if session is None else f(session)

def create_alias_message(name_to_aliases):
    word_to_feature_list = dict((k, ', '.join([feature.gene_name if feature.gene_name is not None else feature.name for feature in v])) for (k, v) in name_to_aliases.iteritems())
                             
    return ', '.join([k + '=(' + v + ')' for (k, v) in word_to_feature_list.iteritems()])

def create_feature_message(name_to_feature):
    return ', '.join([k for k in name_to_feature.keys()])

def create_not_genes_message(not_genes):
    return ', '.join(not_genes)

def find_genes_in_abstract(pubmed_id, session=None):
    """
    Convert a list of gene_names to a mapping between those gene_names and features.
    """            
    
    from model_old_schema.reference import RefTemp

    def f(session): 
        r = get_first(RefTemp, pubmed_id=pubmed_id, session=session)
        a = str(r.abstract).lower().translate(string.maketrans("",""), string.punctuation)
        words = [word.upper() for word in a.split()]
        
        return validate_genes(words, session=session)
            
    return f if session is None else f(session)

class HistoryEntry():
    def __init__(self, date):
        self.date = date
        self.ref_count = 0
        self.refbad_count = 0
        
    def inc_ref_count(self):
        self.ref_count = self.ref_count + 1
    
    def inc_refbad_count(self):
        self.refbad_count = self.refbad_count + 1
    

def get_recent_history(session=None):
    """
    Get a user's recent history.
    """       
    from model_old_schema.reference import Reference, RefBad

    def f(session):
        min_date = datetime.date.today() - datetime.timedelta(days=10)
        refs = session.query(Reference).filter(Reference.date_created >= min_date).filter_by(created_by = session.user)
        refbads = session.query(RefBad).filter(RefBad.date_created >= min_date).filter_by(created_by = session.user)
        
        history = {}
        today = datetime.date.today()
        for i in range(10):
            new_date = today - datetime.timedelta(days=i)  
            history[new_date] = HistoryEntry(new_date)

        for ref in refs:
            if ref.date_created in history:
                history[ref.date_created].inc_ref_count()
        
        for refbad in refbads:
            if refbad.date_created in history:
                history[refbad.date_created].inc_refbad_count()
        return history
        
    return f if session is None else f(session)