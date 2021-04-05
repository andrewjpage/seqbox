"""
SQLAlchemy : Using ORM(Oject Relational Mapper)
"""
from datetime import datetime
from app import db, login
from flask_login import UserMixin
from sqlalchemy.orm import backref # relationship
from sqlalchemy.schema import Sequence
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """This is a Class for User inherits from db.Model,a base class for all models from Flask-SQLAlchemy.
    
    Arguments:
        UserMixin {class} --[ This provides default implementations for the methods that Flask-Login expects user objects to have.]
        db {object} -- [Object that represents the database.]
    
    """
    # These class variables define the column properties
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # establishes a relationship between User and Post
    # backref adds a new property to the Post class, Post.author will point to a User
    # lazy defines when sqlalchemy will load data from the database
    # dynamic returns a query object which you can apply further selects to
    # dynamic is an unusual choice according to here
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        """[The __repr__ method tells Python how to print objects of this class.]
        
        Returns:
            [string] -- [return User model representation. ]
        """
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        """[The set_password method to hash ad store a password in the User model.]
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """[The check_password method to verify the password.  ]
        
        Returns:
            [str] -- [Returns True if the password matched, False otherwise.]
        """
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    """[The @login.user_loader decorated function is used by Flask-Login to convert a stored user ID to an actual user instance.
    The user loader callack function receives a user identifier as a Unicode string the return value of the function 
    must be the user object if available or None otherwise. ]  
    
    """
    return User.query.get(int(id))


class Post(db.Model):
    """[summary]
    
    Arguments:
        db {[type]} -- [description]ll
    
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # user.id here refers to user table, id column
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        """[summary]
        
        Returns:
            [type] -- [description]
        """
        return '<Post {}>'.format(self.body)


class ReadSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.VARCHAR(32), comment="read set type i.e. is it Illumina, nanopore, etc.")
    seqbox_id = db.Column(db.Integer, Sequence("seqbox_id"), comment="SeqBox id, incrementing integer id to uniquely "
                                                                     "identify this read set")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    read_set_filename = db.Column(db.VARCHAR(60), comment="what is the filename of the read set (without R1/R2 for "
                                                          "Illumina data)")
    read_set_name = db.Column(db.VARCHAR(60), comment="the full name of this read set i.e. "
                                                      "{read_set_id}-{isolate.isolate_identifier}")
    mykrobes = db.relationship("Mykrobe", backref=backref("read_set", passive_updates=True,
                                                          passive_deletes=True))
    isolate_id = db.Column(db.Integer, db.ForeignKey("isolate.id", onupdate="cascade", ondelete="set null"),
                           nullable=True)
    illumina_read_sets = db.relationship("IlluminaReadSet", backref="readset")
    nanopore_read_sets = db.relationship("NanoporeReadSet", backref="readset")
    # @hybrid_property
    # def read_set_id(self):
    #     return self.illumina_read_set_id or self.nanopore_read_set_id

    def __repr__(self):
        return f"ReadSet(id: {self.id}, seqbox_id: {self.seqbox_id}, type: {self.type})"


class IlluminaReadSet(db.Model):

    """[Define model 'Sample' mapped to table 'sample']
    Arguments:
        db {[type]} -- [description]
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    read_set_id = db.Column(db.Integer, db.ForeignKey("read_set.id"))
    # illumina_batch = db.Column(db.VARCHAR(50), db.ForeignKey("illumina_batch.id", onupdate="cascade",
    #                                                          ondelete="set null"), nullable=True, comment="")
    # illumina_batches = db.relationship("IlluminaBatch", backref=backref("illumina_read_set", passive_updates=True,
    #                                                                     passive_deletes=True))
    path_r1 = db.Column(db.VARCHAR(60))
    path_r2 = db.Column(db.VARCHAR(60))
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)

    def __repr__(self):
        return f"IlluminaReadSet({self.id}, {self.path_r1})"


class NanoporeReadSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    read_set_id = db.Column(db.Integer, db.ForeignKey("read_set.id"))
    path_fast5 = db.Column(db.VARCHAR(60))
    path_fastq = db.Column(db.VARCHAR(60))
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    # nanopore_batch = db.Column(db.VARCHAR(50), db.ForeignKey("nanopore_batch.id", onupdate="cascade",
    # ondelete="set null"), nullable=True)
    # num_reads = db.Column()

    def __repr__(self):
        return f"NanoporeReadSet({self.id}, {self.path_fastq})"


class Mykrobe(db.Model):
    """[Define model 'Mykrobe' mapped to table 'mykrobe']

    Returns:
        [type] -- [description]
    """
    read_set_id = db.Column(db.Integer, db.ForeignKey("read_set.id", onupdate="cascade",
                                                               ondelete="set null"), nullable=True)
    id = db.Column(db.Integer, primary_key=True)
    # seqbox_id = db.Column(db.Integer, db.ForeignKey("illumina_read_set.seqbox_id", onupdate="cascade",
    # ondelete="set null"), nullable=True)
    mykrobe_version = db.Column(db.VARCHAR(50))
    phylo_grp = db.Column(db.VARCHAR(60))
    phylo_grp_covg = db.Column(db.CHAR)
    phylo_grp_depth = db.Column(db.CHAR)
    species = db.Column(db.VARCHAR(50))
    species_covg = db.Column(db.CHAR)
    species_depth = db.Column(db.CHAR)
    lineage = db.Column(db.VARCHAR(50))
    lineage_covg = db.Column(db.CHAR)
    lineage_depth = db.Column(db.CHAR)
    susceptibility = db.Column(db.VARCHAR(50))
    variants = db.Column(db.VARCHAR(80))
    genes = db.Column(db.VARCHAR(100))
    drug = db.Column(db.VARCHAR(90))

    def __repr__(self):
        return f'<Mykrobe {self.id}, {self.read_set_id}, {self.mykrobe_version}, {self.species})'

    # from here https://stackoverflow.com/questions/57040784/sqlalchemy-foreign-key-to-multiple-tables
    # alternative ways of doing it https://stackoverflow.com/questions/7844460/foreign-key-to-multiple-tables



class Isolate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isolate_identifier = db.Column(db.VARCHAR(30), comment="Lab identifier for this isolate", )
    species = db.Column(db.VARCHAR(120), comment="Putative species of this isolate")
    sample_type = db.Column(db.VARCHAR(60), comment="what sample type is it from? ")
    patient_identifier = db.Column(db.VARCHAR(30), comment="the identifier for the patient this isolate came from")
    date_collected = db.Column(db.DATETIME)
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    location = db.Column(db.VARCHAR(50), db.ForeignKey("location.id_location", onupdate="cascade", ondelete="set null"),
                         nullable=True)
    locations = db.relationship("Location", backref=backref("sample", passive_updates=True, passive_deletes=True))
    read_sets = db.relationship("ReadSet", backref="isolate")
    studies = db.relationship("Study", secondary="isolate_study")
    academic_group = db.Column(db.VARCHAR(60), comment="The name of the academic group this isolate belongs to")
    institution = db.Column(db.VARCHAR(60), comment="The institution this isolate originated at. Specifically, the "
                                                    "institution which assigned the isolate_identifier.")

    def __repr__(self):
        return f"Sample({self.id}, {self.isolate_identifier}, {self.species})"

class IlluminaBatch(db.Model):
    """[Define model 'Batch' mapped to table 'batch']
    
    Arguments:
        db {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.VARCHAR(30), primary_key=True)
    name = db.Column(db.VARCHAR(50))
    date_run = db.Column(db.DATE)
    instrument = db.Column(db.VARCHAR(250))
    # primer = db.Column(db.VARCHAR(100))
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    library_prep_method = db.Column(db.VARCHAR(250))
    dna_extraction_method = db.Column(db.VARCHAR(250))
    
    def __repr__(self):
        return '<Batch {}>'.format(self.name)

class NanoporeBatch(db.Model):
    id = db.Column(db.VARCHAR(30), primary_key=True)
    name = db.Column(db.VARCHAR(50))
    date_run = db.Column(db.DATE)
    instrument = db.Column(db.VARCHAR(250))
    library_prep_method = db.Column(db.VARCHAR(250))
    dna_extraction_method = db.Column(db.VARCHAR(250))

    def __repr__(self):
        return '<Batch {}>'.format(self.name)

class Location(db.Model):
    """[Define model 'Location' mapped to table 'location']
    
    Arguments:
        db {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    id_location = db.Column(db.VARCHAR(25),primary_key=True)
    continent = db.Column(db.VARCHAR(80))
    country = db.Column(db.VARCHAR(60))
    province = db.Column(db.VARCHAR(40))
    city = db.Column(db.VARCHAR(50))
   

    def __repr__(self):
        return '<Location {}>'.format(self.continent)

class Result1(db.Model):
    """[Define model 'Result1' mapped to table 'result1']
    
    Arguments:
        db {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    id_result1 = db.Column(db.Integer,primary_key=True)
    qc = db.Column(db.VARCHAR(60))
    ql = db.Column(db.VARCHAR(60))
    description = db.Column(db.VARCHAR(250))
    snapper_variants = db.Column(db.Integer)
    snapper_ignored = db.Column(db.Integer)
    num_heterozygous = db.Column(db.Integer)
    mean_depth = db.Column(db.CHAR)
    coverage = db.Column(db.CHAR)
   
    def __repr__(self):
        return '<Result1 {}>'.format(self.qc)


class Study(db.Model):

    """[Define model 'Study' mapped to table 'study']
    
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    study_details = db.Column(db.VARCHAR(80))
    isolates = db.relationship("Isolate", secondary="isolate_study")
    
    def __repr__(self):
        return '<Study {}>'.format(self.result_study)


class IsolateStudy(db.Model):
    """[Define model 'Sample_study' mapped to table 'sample_study']
    
    Returns:
        [type] -- [description]
    """
    # id = db.Column(db.Integer, primary_key=True)
    isolate_id = db.Column(db.VARCHAR(40), db.ForeignKey("isolate.id"), primary_key=True)
    study_id = db.Column(db.VARCHAR(50), db.ForeignKey("study.id"), primary_key=True)
    
    def __repr__(self):
        return '<Sample_study {}>'.format(self.id_sample)

