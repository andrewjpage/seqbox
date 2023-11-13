# Test that you can connect to each model and retrieve all data.
# This checks every model can be loaded, that all rows in the database for a model can have objects created
# and every variable/column can be accessed without error.
import sys
import os
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import User, ReadSetBatch, ReadSet, ReadSetIllumina, ReadSetNanopore, Mykrobe, Sample, Culture, Extraction, TilingPcr, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, RawSequencingBatch, SampleSource, Project, Groups, CovidConfirmatoryPcr, PcrResult, PcrAssay, ArticCovidResult, PangolinResult, Batch, Location, Result1, Sample_project

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsModels(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_loading_models(self):
        # Get a list of all models in the models module
        model_names = [User, 
                        ReadSetBatch,
                        ReadSet,
                        ReadSetIllumina,
                        ReadSetNanopore,
                        Mykrobe,
                        Sample,
                        Culture,
                        Extraction,
                        TilingPcr,
                        RawSequencing,
                        RawSequencingNanopore,
                        RawSequencingIllumina,
                        RawSequencingBatch,
                        SampleSource,
                        Project,
                        Groups,
                        CovidConfirmatoryPcr,
                        PcrResult,
                        PcrAssay,
                        ArticCovidResult,
                        PangolinResult,
                        Batch,
                        Location,
                        Result1,
                        Sample_project]
        all_models = [cls for cls in model_names if isinstance(cls, type)]
        
        # Print the names of all modelsn
        for model in all_models:
            print('Checking model: '+ str(model.__name__))

            # Get all rows from the MyModel table
            all_rows = model.query.all()
            # get all of the columns/attributes from the model
            columns = model.__table__.columns.keys()

            accesses = []
            # Now all_rows is a list of MyModel objects, each representing a row in the table
            for row in all_rows:
                for column in columns:
                    try:
                        access = getattr(row, column)
                        # this is purely here to make sure the preceeding line doesnt get optimised out by the interpreter.
                        accesses.append(access)
                    except:
                        print("There is an issue accessing the data (model, row, column): ", model.__name__, row, column)

t = TestUtilsModels()
t.test_loading_models()
