
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Mykrobe, Project #,Sample_project #Sample, Batch, Location, Result1

class LoginForm(FlaskForm):
   
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class SampleForm(FlaskForm):
    
    id_sample = StringField('id_sample', validators=[DataRequired()])
    num_reads = StringField('num_reads', validators=[DataRequired()])
    date_time = DateField('date_time')
    organism = StringField('organism')
    path_r1 = StringField('path_r1')
    path_r2 = StringField('path_r2')
    batch =  StringField('batch')
    location = StringField('location')
    result1 = StringField('result1')
    mykrobe = StringField('mykrobe')

    submit = SubmitField('Validate')
    
    def validate_id_sample(self, id_sample):
        sample = Sample.query.filter_by(id_sample=id_sample.data).first()
        if sample is not None:
            raise ValidationError('Please use a different id_sample.')
    
    def validate_num_reads(self,num_reads):
        sample =Sample.query.filter_by(num_reads=num_reads.data).first()
        if sample is not None:
            raise ValidationError('Please use a different num_reads.')


    
    
        
class BatchForm(FlaskForm):

    id_batch = StringField('id_batch', validators=[DataRequired()])
    name_batch = StringField('name_batch', validators=[DataRequired()])
    date_batch = StringField('date_batch')
    instrument = StringField('instrument')
    primer = StringField('primer')
    
    submit = SubmitField('Validate')

    def validate_id_batch(self, id_batch):
        batch = Batch.query.filter_by(id_batch=id_batch.data).first()
        if batch is not None:
            raise ValidationError('Please use a different id_batch.')

    def validate_name_batch(self, name_batch):
        batch = Batch.query.filter_by(name_batch=name_batch.data).first()
        if batch is not None:
            raise ValidationError('Please use a different name_batch.')

    
class LocationForm(FlaskForm):

    id_location= StringField('id_location', validators=[DataRequired()])
    continent = StringField('continent')
    country = StringField('country')
    province = StringField('province')
    city = StringField('city')

    submit = SubmitField('Validate')

    def validate_id_location(self, id_location):

        location = Location.query.filter_by(id_location=id_location.data).first()
        if location is not None:
            raise ValidationError('Please use a different id_location.')

    
class Result1Form(FlaskForm):

    id_result1= StringField('id_result1', validators=[DataRequired()])
    qc = StringField('qc')
    ql = StringField('ql')
    description = StringField('description')
    snapper_variants = StringField('snapper_variants')
    snapper_ignored = StringField('snapper_ignored')
    num_heterozygous = StringField('num_heterozygous')
    mean_depth = StringField('mean_depth')
    coverage = StringField('coverage')

    submit = SubmitField('Validate')

    def validate_id_result1(self, id_result1):
        result1 = Result1.query.filter_by(id_result1=id_result1.data).first()
        if result1 is not None:
            raise ValidationError('Please use a different id_result1.')

    
class MykrobeForm(FlaskForm):

    id_mykrobe= StringField('id_mykrobe', validators=[DataRequired()])
    mykrobe_version = StringField('mykrobe_version')
    phylo_grp = StringField('phylo_grp')
    phylo_grp_covg = StringField('phylo_grp_covg')
    phylo_grp_depth = StringField('phylo_grp_depth')
    species = StringField('species')
    species_covg = StringField('species_covg')
    species_depth = StringField('species_depth')
    lineage = StringField('lineage')
    lineage_covg = StringField('lineage_covg')
    lineage_depth = StringField('lineage_depth')
    susceptibility = StringField('susceptibility')
    variants = StringField('variants')
    genes = StringField('genes')
    drug = StringField('drug')

    submit = SubmitField('Validate')

    def validate_id_mykrobe(self, id_mykrobe):
        mykrobe_result = Mykrobe.query.filter_by(id_mykrobe=id_mykrobe.data).first()
        if mykrobe_result is not None:
            raise ValidationError('Please use a different id_mykrobe.')

class ProjectForm(FlaskForm) :

    id_project = StringField('id_project', validators=[DataRequired()])
    date_project = StringField('date_project')
    result_project = StringField('result_project')
    submit = SubmitField('Validate')
    
    def validate_id_project(self, id_project):

        project = Project.query.filter_by(id_project=id_project.data).first()
        if project is not None:
            raise ValidationError('Please use a different id_project.')

class Sample_projectForm(FlaskForm):
    
    id_project = StringField('id_project', validators=[DataRequired()])
    id_sample = StringField('id_sample', validators=[DataRequired()])
    submit = SubmitField('Validate')

    def validate_id_project(self, id_project):
        sample_project = Sample_project.query.filter_by(id_project=id_project.data).first()
        if sample_project is not None:
            raise ValidationError('Please use a different id_project.')

    def validate_id_sample(self, id_sample):
        sample_project = Sample_project.query.filter_by(id_sample=id_sample.data).first()
        if sample_project is not None:
            raise ValidationError('Please use a different id_sample.')