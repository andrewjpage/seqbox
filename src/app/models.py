"""
SQLAlchemy : Using ORM(Oject Relational Mapper)
"""
from datetime import datetime
from app import db, login
from flask_login import UserMixin
from sqlalchemy.orm import backref  # relationship
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
    raw_sequencing_id = db.Column(db.Integer,
                                  db.ForeignKey("raw_sequencing.id", onupdate="cascade", ondelete="set null"),
                                  nullable=True)
    # the Sequence won't work until port to postgres
    seqbox_id = db.Column(db.Integer, db.Sequence("seqbox_id"), comment="SeqBox id, incrementing integer id to "
                                                                        "uniquely identify this read set")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    read_set_filename = db.Column(db.VARCHAR(60), comment="what is the filename of the read set (without R1/R2 for "
                                                          "Illumina data)")
    read_set_name = db.Column(db.VARCHAR(60), comment="the full name of this read set i.e. "
                                                      "{read_set_id}-{sample.sample_identifier}")
    mykrobes = db.relationship("Mykrobe", backref=backref("read_set", passive_updates=True,
                                                          passive_deletes=True))

    read_set_illumina = db.relationship("ReadSetIllumina", backref="readset", uselist=False)
    read_set_nanopore = db.relationship("ReadSetNanopore", backref="readset", uselist=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("read_set_batch.id"))

    # @hybrid_property
    # def read_set_id(self):
    #     return self.illumina_read_set_id or self.nanopore_read_set_id

    def __repr__(self):
        return f"ReadSet(id: {self.id}, seqbox_id: {self.seqbox_id}, read_set_filename: {self.read_set_filename})"


class ReadSetIllumina(db.Model):
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
        return f"ReadSetIllumina({self.id}, {self.path_r1})"


class ReadSetNanopore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    read_set_id = db.Column(db.Integer, db.ForeignKey("read_set.id"))
    path_fastq = db.Column(db.VARCHAR(60))
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    basecaller = db.Column(db.VARCHAR(60))

    # nanopore_batch = db.Column(db.VARCHAR(50), db.ForeignKey("nanopore_batch.id", onupdate="cascade",
    # ondelete="set null"), nullable=True)
    # num_reads = db.Column()

    def __repr__(self):
        return f"ReadSetNanopore({self.id}, {self.path_fastq})"


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


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_identifier = db.Column(db.VARCHAR(30), comment="Lab identifier for the sample which DNA was extracted from. "
                                                          "Has to be unique within a group.")
    sample_type = db.Column(db.VARCHAR(60), comment="What was DNA extracted from? An isolate, clinical sample (for "
                                                    "covid), a plate sweep, whole stools, etc.")
    species = db.Column(db.VARCHAR(120), comment="Putative species of this sample, if known/appropriate.")
    sample_source_id = db.Column(db.ForeignKey("sample_source.id"))
    day_collected = db.Column(db.Integer, comment="day of the month this was collected")
    month_collected = db.Column(db.Integer, comment="month this was collected")
    year_collected = db.Column(db.Integer, comment="year this was collected")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    processing_institution = db.Column(db.VARCHAR(60), comment="The institution which processed the sample.")
    # locations = db.relationship("Location", backref=backref("sample", passive_updates=True, passive_deletes=True))
    extractions = db.relationship("Extraction", backref="sample")


    def __repr__(self):
        return f"Sample({self.id}, {self.sample_identifier}, {self.species})"


class Extraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.ForeignKey("sample.id"))
    extraction_identifier = db.Column(db.Integer, comment="An identifier to differentiate multiple extracts from the "
                                                          "ame sample on the same day. It will usually be 1, but if "
                                                          "this is the second extract done on this sample on this day, "
                                                          "it needs to be 2 (and so on).")
    extraction_machine = db.Column(db.VARCHAR(60), comment="E.g. QiaSymphony, manual")
    extraction_kit = db.Column(db.VARCHAR(60), comment="E.g. Qiasymphony Minikit")
    what_was_extracted = db.Column(db.VARCHAR(60), comment="E.g. DNA, RNA")
    date_extracted = db.Column(db.DATETIME, comment="Date this extract was done")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    processing_institution = db.Column(db.VARCHAR(60), comment="The institution which did the DNA extraction.")
    raw_sequencing = db.relationship("RawSequencing", backref="extraction")

    def __repr__(self):
        return f"Extraction(id={self.id}, sample.id={self.sample_id}, date_extracted={self.date_extracted})"


class TilingPcr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraction_id = db.Column(db.ForeignKey("extraction.id"))
    number_of_cycles = db.Column(db.Integer, comment="Number of PCR cycles")
    date_run = db.Column(db.DATETIME, comment="Date this PCR was done")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)

    def __repr__(self):
        return f"TilingPcr(id={self.id}, extraction.id={self.extraction_id})"


class RawSequencing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraction_id = db.Column(db.ForeignKey("extraction.id"))
    data_storage_device = db.Column(db.VARCHAR(64), comment="which machine is this data stored on?")
    sequencing_type = db.Column(db.VARCHAR(32), comment="Sequencing type i.e. is it Illumina, nanopore, etc.")
    read_sets = db.relationship("ReadSet", backref="raw_sequencing")
    raw_sequencing_nanopore = db.relationship("RawSequencingNanopore", backref="raw_sequencing", uselist=False)
    raw_sequencing_illumina = db.relationship("RawSequencingIllumina", backref="raw_sequencing", uselist=False)

    def __repr__(self):
        return f"RawSequencing(id={self.id}, extraction.id={self.extraction_id})"


class RawSequencingNanopore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raw_sequencing_id = db.Column(db.ForeignKey("raw_sequencing.id"))
    path_fast5 = db.Column(db.VARCHAR(96))

    def __repr__(self):
        return f"RawSequencingNanopore(id={self.id}, path_fast5={self.path_fast5})"


class RawSequencingIllumina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raw_sequencing_id = db.Column(db.ForeignKey("raw_sequencing.id"))
    path_r1 = db.Column(db.VARCHAR(96))
    path_r2 = db.Column(db.VARCHAR(96))

    def __repr__(self):
        return f"RawSequencingIllumina(id={self.id}, path_r1={self.path_r1})"


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


sample_source_project = db.Table("sample_source_project",
                                  db.Column("sample_source_id", db.Integer, db.ForeignKey("sample_source.id"),
                                            primary_key=True),
                                  db.Column("project_id", db.Integer, db.ForeignKey("project.id"), primary_key=True)
                                  )


class SampleSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_source_identifier = db.Column(db.VARCHAR(30), comment="the identifier for the sample source this sample "
                                                                  "came from, e.g. if it's a stool sample, then "
                                                                 "what is the identifier of the patient it came from")
    sample_source_type = db.Column(db.VARCHAR(60), comment="what type of sample source did it come from? i.e. what "
                                                           "does the sample source identifier identify? is it a patient"
                                                           "or a visit (like tyvac/strataa), or a sampling location for"
                                                           " an environmental sample")
    # todo - how do we handle multiple picks from same plate?
    # projects = db.relationship("Project", secondary="sample_source_project", backref=db.backref("projects"))
    projects = db.relationship("Project", secondary="sample_source_project", backref="sample_source")
    samples = db.relationship("Sample", backref="sample_source")
    latitude = db.Column(db.Float(), comment="Latitude of sample source if known")
    longitude = db.Column(db.Float(), comment="Longitude of sample source origin if known")
    country = db.Column(db.VARCHAR(60), comment="country of origin")
    location_first_level = db.Column(db.VARCHAR(40), comment="Highest level of organisation within country e.g. region,"
                                                             " province, state")
    location_second_level = db.Column(db.VARCHAR(50), comment="Second highest level of organisation e.g. county, "
                                                              "district Malawi), large city/metro area")
    location_third_level = db.Column(db.VARCHAR(50), comment="Third highest level of organisation e.g. district "
                                                             "(UK/VN), township (MW)")


class Project(db.Model):
    """[Define model 'project' mapped to table 'project']

    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.VARCHAR(32), comment="You can think about this as 'what study got ethics for this "
                                                     "sample to be taken'")
    group_name = db.Column(db.VARCHAR(60), comment="The name of the group running this project (again, think about"
                                                   "this in context of ethics permission).")
    date_added = db.Column(db.DATETIME, default=datetime.utcnow)
    institution = db.Column(db.VARCHAR(60), comment="The name of the institution running this project.")
    project_details = db.Column(db.VARCHAR(160))
    __table_args__ = (UniqueConstraint('project_name', 'group_name', name='_projectname_group_uc'),)

    def __repr__(self):
        return f"Project(id: {self.id}, details: {self.project_name})"



