'''
Created on Dec 4, 2012

@author: kpaskov
'''
from model_old_schema.model import get_first, get
import datetime
import string

    
def get_feature_by_name(name, session=None):
    """
    Get a feature by its name.
    """     
    
    from model_old_schema.feature import Feature

    def f(session):
        feature = get_first(Feature, session, name=name.upper())
        if feature is not None and not feature.type == 'chromosome':
            return feature
        
        
        feature = get_first(Feature, session, gene_name=name.upper())
        if feature is not None and not feature.type == 'chromosome':
            return feature
        
        return None
    
    return f if session is None else f(session)

def get_features_by_alias(name, session=None):
    """
    Get a feature by its alias.
    """  
    
    from model_old_schema.feature import Feature

    def f(session):
        all_possible = set()

        features = session.query(Feature).filter(Feature.alias_names.contains(name.upper())).all()
        all_possible.update(features)
        
        all_possible = [feature for feature in all_possible if not feature.type == 'chromosome']
 
        return all_possible
    
    return f if session is None else f(session)
    
def get_reftemps(session=None):
    
    from model_old_schema.reference import RefTemp

    def f(session):
        return get(RefTemp, session)
    
    return f if session is None else f(session)

def validate_genes(gene_names, session=None):
    """
    Convert a list of gene_names to a mapping between those gene_names and features.
    """            
    
    from model_old_schema.feature import Feature

    def f(session):
        if gene_names is not None and len(gene_names) > 0:
            upper_gene_names = [x.upper() for x in gene_names]
            fs = set(session.query(Feature).filter(Feature.name.in_(upper_gene_names)).all())
            fs.update(session.query(Feature).filter(Feature.gene_name.in_(upper_gene_names)).all())
                
            name_to_feature = {}
            for f in fs:
                name_to_feature[f.name] = f
                name_to_feature[f.gene_name] = f
                
            extraneous_names = name_to_feature.keys()
            for name in upper_gene_names:
                if name.upper() in extraneous_names:
                    extraneous_names.remove(name.upper())
                    
            for name in extraneous_names:
                del name_to_feature[name]
                 
            return name_to_feature
        else:
            return {}
        
    return f if session is None else f(session)

def find_genes_in_abstract(pubmed_id, session=None):
    """
    Convert a list of gene_names to a mapping between those gene_names and features.
    """            
    
    from model_old_schema.reference import RefTemp

    def f(session): 
        words_tried = set()       
        name_to_feature = {}
        alias_to_features = {}
        
        r = get_first(RefTemp, pubmed_id=pubmed_id, session=session)
        a = str(r.abstract).lower().translate(string.maketrans("",""), string.punctuation)
        words = [word.upper() for word in a.split()]
        
        for word in words:
            if not word in words_tried:
                fs = get_features_by_alias(word, session)
                f = get_feature_by_name(word, session)

                if len(fs) > 0:
                    if f is not None:
                        fs.append(f)
                    alias_to_features[word] = fs
                elif f is not None:
                    name_to_feature[word] = f
                words_tried.add(word)
        return {"name":name_to_feature, "alias":alias_to_features}
        
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
        refs = session.query(Reference).filter_by(created_by = session.user).filter(Reference.date_created >= min_date)
        refbads = session.query(RefBad).filter_by(created_by = session.user).filter(Reference.date_created >= min_date)
        
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