"""
SQLAlchemy : Using ORM(Oject Relational Mapper)
"""
from datetime import datetime
from app import db, login
from flask_login import UserMixin
from sqlalchemy.orm import backref # relationship
from sqlalchemy.schema import Sequence, UniqueConstraint
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
    # posts = db.relationship('Post', backref='author', lazy='dynamic')

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


class ReadSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.VARCHAR(32), comment="read set type i.e. is it Illumina, nanopore, etc.")
    # the Sequence won't work until port to postgres
    seqbox_id = db.Column(db.Integer, db.Sequence("seqbox_id"), comment="SeqBox id, incrementing integer id to "
                                                                        "uniquely identify this read set")
    # seqbox_id = db.Column(db.Integer, comment="SeqBox id, incrementing integer id to uniquely identify this read set",
    #                       sqlite_autoincrement=True)
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    read_set_filename = db.Column(db.VARCHAR(60), comment="what is the filename of the read set (without R1/R2 for "
                                                          "Illumina data)")
    read_set_name = db.Column(db.VARCHAR(60), comment="the full name of this read set i.e. "
                                                      "{read_set_id}-{isolate.isolate_identifier}")
    mykrobes = db.relationship("Mykrobe", backref=backref("read_set", passive_updates=True,
                                                          passive_deletes=True))
    isolate_id = db.Column(db.Integer, db.ForeignKey("isolate.id", onupdate="cascade", ondelete="set null"),
                           nullable=True)
    illumina_read_sets = db.relationship("IlluminaReadSet", backref="readset", uselist=False)
    nanopore_read_sets = db.relationship("NanoporeReadSet", backref="readset", uselist=False)
    dna_extraction_method = db.Column(db.VARCHAR(64))
    batch_id = db.Column(db.Integer, db.ForeignKey("read_set_batch.id"))
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
    isolate_identifier = db.Column(db.VARCHAR(30), comment="Lab identifier for this isolate")
    species = db.Column(db.VARCHAR(120), comment="Putative species of this isolate")
    sample_type = db.Column(db.VARCHAR(60), comment="what sample type is it from? E.g. blood, stool, etc.")
    patient_id = db.Column(db.ForeignKey("patient.id"))

    # date_collected = db.Column(db.DATETIME)
    day_collected = db.Column(db.Integer, comment="day of the month this was collected")
    month_collected = db.Column(db.Integer, comment="month this was collected")
    year_collected = db.Column(db.Integer, comment="year this was collected")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    latitude = db.Column(db.Float(), comment="Latitude of isolate origin if known")
    longitude = db.Column(db.Float(), comment="Longitude of isolate origin if known")
    country = db.Column(db.VARCHAR(60), comment="country of origin")
    location_first_level = db.Column(db.VARCHAR(40), comment="Highest level of organisation within country e.g. region,"
                                                             " province, state")
    location_second_level = db.Column(db.VARCHAR(50), comment="Second highest level of organisation e.g. county, "
                                                              "district Malawi), large city/metro area")
    location_third_level = db.Column(db.VARCHAR(50), comment="Third highest level of organisation e.g. district "
                                                             "(UK/VN), township (MW)")
    # locations = db.relationship("Location", backref=backref("sample", passive_updates=True, passive_deletes=True))
    read_sets = db.relationship("ReadSet", backref="isolate")


    institution = db.Column(db.VARCHAR(60), comment="The institution this isolate originated at. Specifically, the "
                                                    "institution which assigned the isolate_identifier.")
    ## NOTE - is the isolate identifier unique within a group or within a project?

    def __repr__(self):
        return f"Sample({self.id}, {self.isolate_identifier}, {self.species})"


class ReadSetBatch(db.Model):
    """[Define model 'Batch' mapped to table 'batch']
    
    Arguments:
        db {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(50))
    date_run = db.Column(db.DATE)
    instrument = db.Column(db.VARCHAR(64))
    instrument_name = db.Column(db.VARCHAR(64), comment="For MLW machines, which exact machine was it run on")
    # primer = db.Column(db.VARCHAR(100))
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    library_prep_method = db.Column(db.VARCHAR(64))
    sequencing_centre = db.Column(db.VARCHAR(64), comment="E.g. Sanger, CGR, MLW, etc.")
    read_sets = db.relationship("ReadSet", backref="batch")
    
    def __repr__(self):
        return '<Batch {}>'.format(self.name)


# class Patient(db.Model):
#     # assuming that each patient identifier is unique wihtin a project
#     id = db.Column(db.Integer, primary_key=True)
#     group_id = db.Column(db.Integer, db.ForeignKey("group.id"))
#     patient_identifier = db.Column(db.VARCHAR(30))
#     isolates = db.relationship("Isolate", backref="patient")
#     __table_args__ = (UniqueConstraint('project_id', 'patient_identifier', name='_projectid_patientidentifier_uc'),)
#     # project = db.Column(db.ForeignKey("project.id"))
#     # projects = db.relationship("Project", secondary="patient_project", backref=db.backref("patients"))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_identifier = db.Column(db.VARCHAR(30), comment="the identifier for the patient this isolate came from")
    projects = db.relationship("Project", secondary="patient_project", backref=db.backref("projects"))
    isolates = db.relationship("Isolate", backref="patient")


class Project(db.Model):
    """[Define model 'project' mapped to table 'project']

    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.VARCHAR(32), comment="You can think about this as 'what study got ethics for this "
                                                     "isolate to be taken'")
    group_name = db.Column(db.VARCHAR(60), comment="The name of the group running this project (again, think about"
                                                   "this in context of ethics permission).")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    institution = db.Column(db.VARCHAR(60), comment="The name of the institution running this project.")
    project_details = db.Column(db.VARCHAR(160))
    # patients = db.relationship("patient", backref="project")
    __table_args__ = (UniqueConstraint('project_name', 'group_name', name='_projectname_group_uc'),)
    # isolates = db.relationship("Isolate", secondary="isolate_project")
    
    def __repr__(self):
        return f"Project(id: {self.id}, details: {self.project_name})"


patient_project = db.Table("patient_project",
                         db.Column("patient_id", db.Integer, db.ForeignKey("patient.id"), primary_key=True),
                         db.Column("project_id", db.Integer, db.ForeignKey("project.id"), primary_key=True)
                         )

#
# patient_project = db.Table("patient_project",
#                          db.Column("patient_id", db.Integer, db.ForeignKey("patient.id"), primary_key=True),
#                          db.Column("project_id", db.Integer, db.ForeignKey("project.id"), primary_key=True)
#                          )
