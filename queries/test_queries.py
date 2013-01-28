from model_old_schema.model import get_first
from model_old_schema.test_model import ModelCreationMixin, test_validity, \
    validate_feature, validate_reftemp, validate_refbad, validate_ref
from queries.associate import associate, Task, TaskType
from queries.misc import get_feature_by_name, get_reftemps, validate_genes, \
    get_recent_history
from queries.move_ref import move_refbad_to_reftemp, move_reftemp_to_refbad, \
    move_reftemp_to_ref, move_ref_to_reftemp
from unittest.suite import TestSuite
import unittest


class TestMiscQueries(ModelCreationMixin):
        
    def test_get_feature_by_name(self, feature_id=1971, name='YJL001W', feature_name=None):
        f = get_feature_by_name(name)
        self.model.execute(test_validity(self, f, validate_feature, feature_id=feature_id, feature_name=feature_name))
        
    def test_get_feature_by_name_case(self, feature_id=1971, feature_name='yjl001W'):
        self.test_get_feature_by_name(feature_id, name=feature_name)
        
    def test_get_feature_by_name_genename(self, feature_id=1971, gene_name='PRE3'):
        self.test_get_feature_by_name(feature_id, name=gene_name)
 
    def test_get_reftemps(self):
        rs = self.model.execute(get_reftemps())
        self.assertTrue(len(rs) > 0)
        
    def test_validate_genes(self):
        gene_names = ['YAL002W', 'CEN1', 'SPO7', 'YAL016C-B', 'YAL009W']
        feature_ids = [6102, 2899, 6347, 7398, 6347]

        name_to_feature = self.model.execute(validate_genes(gene_names))
        
        self.assertEqual(len(gene_names), len(name_to_feature))
        for i in range(0, len(gene_names)):
            self.assertEqual(name_to_feature[gene_names[i]].id, feature_ids[i])
            
    def test_get_recent_history(self):
        def f(session):
            h = get_recent_history(session=session)
            for key, event in h.items():
                print key
                print event.ref_count
                print event.refbad_count
            
        self.model.execute(f, commit=False)
   
class TestMoveRefQueries(ModelCreationMixin):
        
    def test_move_refbad_to_reftemp(self, pubmed_id=16830189):
        def f(session):    
            from model_old_schema.reference import RefTemp
            #Move refbad to reftemp and test that move was successful.
            result = move_refbad_to_reftemp(pubmed_id, session)  
            self.assertTrue(result)
            
            #Test that new reftemp is valid.
            reftemp = get_first(RefTemp, pubmed_id=pubmed_id)
            test_validity(self, reftemp, validate_reftemp, session=session, pubmed_id=pubmed_id)
        
        #Because commit=False, the move is not committed to the db.
        self.model.execute(f, commit=False)

    def test_move_reftemp_to_refbad(self, pubmed_id=23220089):
        def f(session):
            from model_old_schema.reference import RefBad
            #Move reftemp to refbad and test that move was successful.
            result = move_reftemp_to_refbad(pubmed_id, session)  
            self.assertTrue(result)
            
            #Test that new refbad is valid.
            refbad = get_first(RefBad, pubmed_id=pubmed_id)
            test_validity(self, refbad, validate_refbad, session=session, pubmed_id=pubmed_id)
        
        #Because commit=False, the move is not committed to the db. 
        self.model.execute(f, commit=False)

    def test_move_reftemp_to_ref(self, pubmed_id=23223634):
        def f(session):
            from model_old_schema.reference import Reference
            #Move reftemp to ref and test that move was successful.
            result = move_reftemp_to_ref(pubmed_id, session)  
            self.assertTrue(result)
            
            #Test that new ref is valid.
            ref = get_first(Reference, pubmed_id=pubmed_id)
            test_validity(self, ref, validate_ref, session=session, pubmed_id=pubmed_id)
        
        #Because commit=False, the move is not committed to the db.
        self.model.execute(f, commit=False)
  
    def test_move_ref_to_reftemp(self, pubmed_id=7962081):
        def f(session):
            from model_old_schema.reference import RefTemp
            #Move ref to reftemp and test that move was successful.
            result = move_ref_to_reftemp(pubmed_id, session)  
            self.assertTrue(result)
            
            #Test that new ref is valid.
            reftemp = get_first(RefTemp, pubmed_id=pubmed_id)
            test_validity(self, reftemp, validate_reftemp, session=session, pubmed_id=pubmed_id)
        
        #Because commit=False, the move is not committed to the db.
        self.model.execute(f, commit=False)
            
class TestAssociate(ModelCreationMixin):
          
    def test_associate(self):
        def f(session):
            pubmed_id = 23105524
            gene_names = ['ACT1', 'CEN1', 'SPO7', 'YAL016C-B', 'YAL009W']
        
            from model_old_schema.reference import Reference

            move_reftemp_to_ref(pubmed_id, session=session)
            name_to_feature = self.model.execute(validate_genes(gene_names))
            tasks = [Task(TaskType.HIGH_PRIORITY, None, "Comment"),
                     Task(TaskType.DELAY, None, "Comment"),
                     Task(TaskType.HTP_PHENOTYPE_DATA, None, "Comment"),
                     Task(TaskType.OTHER_HTP_DATA, None, "Comment"),
                     
                     Task(TaskType.CLASSICAL_PHENOTYPE_INFORMATION, ['ACT1'], "Comment"),
                     Task(TaskType.GO_INFORMATION, ['ACT1'], "Comment"),
                     Task(TaskType.HEADLINE_INFORMATION, ['YAL009W', 'YAL016C-B'], "Comment"),
                     
                     Task(TaskType.ADDITIONAL_LITERATURE, None, "Comment"),
                     Task(TaskType.REVIEWS, None, "Comment")
                     ]
            
            result = associate(pubmed_id, name_to_feature, tasks, session=session)
            self.assertTrue(result)
            
            
            curations = get_first(Reference, session=session, pubmed_id=pubmed_id).curations
            lit_guides = get_first(Reference, session=session, pubmed_id=pubmed_id).litGuides
            
            self.assertEqual(len(curations), 9)
            for curation in curations:
                self.assertTrue(curation.comment is not None)
                
                if curation.task == 'Gene Link':
                    self.assertTrue(False, 'The two Tasks with name Gene Link: ADD_TO_DATABASE and REVIEWS have no genes. They should not have curaitons.')
                   
            self.assertEqual(len(lit_guides), 6)
            for lit_guide in lit_guides:
                if curation.task == 'Reviews':
                    self.assertEqual(len(lit_guide.features), 0)
                
        #Because commit=False, the associations are not committed to the db.
        self.model.execute(f, commit=False)

        
        
if __name__ == '__main__':
    suite = TestSuite()
    suite.addTest(TestMoveRefQueries('test_move_refbad_to_reftemp'))
    unittest.TextTestRunner().run(suite)
    
