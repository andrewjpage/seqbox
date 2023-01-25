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
from sqlalchemy.schema import (CheckConstraint)

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
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

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


class ReadSetBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(60), comment="Name of readset batch.")
    batch_directory = db.Column(db.VARCHAR(128), comment="Original directory where readset batch stored.")
    basecaller = db.Column(db.VARCHAR(60), comment="Basecaller used to generate sequence data.")
    raw_sequencing_batch_id = db.Column(db.Integer,
                                        db.ForeignKey("raw_sequencing_batch.id", onupdate="cascade",
                                                      ondelete="cascade"),
                                        nullable=True)
    readsets = db.relationship("ReadSet", backref=backref("readset_batch", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")


class ReadSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raw_sequencing_id = db.Column(db.Integer,
                                  db.ForeignKey("raw_sequencing.id", onupdate="cascade", ondelete="cascade"))
    readset_batch_id = db.Column(db.Integer, db.ForeignKey("read_set_batch.id", ondelete="cascade", onupdate="cascade"))
    readset_identifier = db.Column(db.Integer, db.Sequence("readset_identifier"), comment="ReadSet identifier id, "
                                                                                          "incrementing integer id to "
                                                                                          "uniquely identify this read "
                                                                                          "set")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    readset_name = db.Column(db.VARCHAR(60), comment="the full name of this read set i.e. "
                                                      "{readset_id}-{sample.sample_identifier}")
    mykrobes = db.relationship("Mykrobe", backref=backref("readset", passive_updates=True,
                                                          passive_deletes=True))
    readset_illumina = db.relationship("ReadSetIllumina", backref=backref("readset", passive_deletes=True), uselist=False)
    readset_nanopore = db.relationship("ReadSetNanopore", backref=backref("readset", passive_deletes=True), uselist=False)
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    data_storage_device = db.Column(db.VARCHAR(64), comment="which machine is this data stored on?")
    include = db.Column(db.VARCHAR(128), comment="Should this readset be included in further analyses?")
    artic_covid_result = db.relationship("ArticCovidResult", backref=backref("readset", passive_deletes=True))

    # @hybrid_property
    # def readset_id(self):
    #     return self.illumina_readset_id or self.nanopore_readset_id

    def __repr__(self):
        return f"ReadSet(id: {self.id}, readset_identifier: {self.readset_identifier}"


class ReadSetIllumina(db.Model):
    """[Define model 'Sample' mapped to table 'sample']
    Arguments:
        db {[type]} -- [description]
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    readset_id = db.Column(db.Integer, db.ForeignKey("read_set.id", ondelete="cascade", onupdate="cascade"))

    # illumina_batch = db.Column(db.VARCHAR(50), db.ForeignKey("illumina_batch.id", onupdate="cascade",
    #                                                          ondelete="set null"), nullable=True, comment="")
    # illumina_batches = db.relationship("IlluminaBatch", backref=backref("illumina_readset", passive_updates=True,
    #                                                                     passive_deletes=True))
    path_r1 = db.Column(db.VARCHAR(250))
    path_r2 = db.Column(db.VARCHAR(250))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"ReadSetIllumina({self.id}, {self.path_r1})"


class ReadSetNanopore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    readset_id = db.Column(db.Integer, db.ForeignKey("read_set.id", ondelete="cascade", onupdate="cascade"))
    path_fastq = db.Column(db.VARCHAR(250))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    basecaller = db.Column(db.VARCHAR(60))
    barcode = db.Column(db.VARCHAR(60))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

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
    readset_id = db.Column(db.Integer, db.ForeignKey("read_set.id", onupdate="cascade", ondelete="cascade"))
    id = db.Column(db.Integer, primary_key=True)
    # readset_identifier = db.Column(db.Integer, db.ForeignKey("illumina_read_set.readset_identifier", onupdate="cascade",
    # ondelete="set null"), nullable=True)
    mykrobe_version = db.Column(db.VARCHAR(50))
    phylo_grp = db.Column(db.VARCHAR(60))
    phylo_grp_covg = db.Column(db.VARCHAR(60))
    phylo_grp_depth = db.Column(db.VARCHAR(60))
    species = db.Column(db.VARCHAR(50))
    species_covg = db.Column(db.VARCHAR(60))
    species_depth = db.Column(db.VARCHAR(60))
    lineage = db.Column(db.VARCHAR(50))
    lineage_covg = db.Column(db.VARCHAR(60))
    lineage_depth = db.Column(db.VARCHAR(60))
    susceptibility = db.Column(db.VARCHAR(50))
    variants = db.Column(db.VARCHAR(80))
    genes = db.Column(db.VARCHAR(100))
    drug = db.Column(db.VARCHAR(90))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f'<Mykrobe {self.id}, {self.readset_id}, {self.mykrobe_version}, {self.species})'
    # from here https://stackoverflow.com/questions/57040784/sqlalchemy-foreign-key-to-multiple-tables
    # alternative ways of doing it https://stackoverflow.com/questions/7844460/foreign-key-to-multiple-tables


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_identifier = db.Column(db.VARCHAR(30), comment="Lab identifier for the sample which DNA was extracted from. "
                                                          "Has to be unique within a group.")
    sample_type = db.Column(db.VARCHAR(60), comment="What was DNA extracted from? An isolate, clinical sample (for "
                                                    "covid), a plate sweep, whole stools, etc.")
    species = db.Column(db.VARCHAR(120), comment="Putative species of this sample, if known/appropriate.")
    sample_source_id = db.Column(db.ForeignKey("sample_source.id", ondelete="cascade", onupdate="cascade"))
    day_collected = db.Column(db.Integer, comment="day of the month this was collected")
    month_collected = db.Column(db.Integer, comment="month this was collected")
    year_collected = db.Column(db.Integer, comment="year this was collected")
    day_received = db.Column(db.Integer, comment="day of the month this was received")
    month_received = db.Column(db.Integer, comment="month this was received")
    year_received = db.Column(db.Integer, comment="year this was received")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    processing_institution = db.Column(db.VARCHAR(60), comment="The institution which processed the sample.")
    # locations = db.relationship("Location", backref=backref("sample", passive_updates=True, passive_deletes=True))
    extractions = db.relationship("Extraction", backref=backref("sample", passive_deletes=True))
    cultures = db.relationship("Culture", backref=backref("sample", passive_deletes=True))
    pcr_results = db.relationship("PcrResult", backref=backref("sample", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"Sample({self.id}, {self.sample_identifier}, {self.species})"


class Culture(db.Model):
    __table_args__ = (
        UniqueConstraint('submitter_plate_id', 'submitter_plate_well', name='_culture_plateid_platewell_uc'),
    )
    id = db.Column(db.Integer, primary_key=True)
    culture_identifier = db.Column(db.VARCHAR(30), comment="An identifier to differentiate multiple cultures from the "
                                                          "same sample on the same day. It will usually be 1, but if "
                                                          "this is the second culture done on this sample on this day, "
                                                          "it needs to be 2 (and so on).")
    date_cultured = db.Column(db.DateTime, comment="Date this culture was done")
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id", ondelete="cascade", onupdate="cascade"))
    extractions = db.relationship("Extraction", backref=backref("culture", passive_deletes=True))
    submitter_plate_id = db.Column(db.VARCHAR(60), comment="The plate ID given by the submitter.")
    submitter_plate_well = db.Column(db.VARCHAR(60), comment="The well ID given by the submitter.")


class Extraction(db.Model):
    __table_args__ = (
        CheckConstraint('(sample_id IS NULL) <> (culture_id IS NULL)', name='foreign_key_xor'),
        UniqueConstraint('submitter_plate_id', 'submitter_plate_well', name='_extraction_plateid_platewell_uc'),
        UniqueConstraint('elution_plate_id', 'elution_plate_well', name='_elution_plateid_platewell_uc')
    )
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.ForeignKey("sample.id", ondelete="cascade", onupdate="cascade"))
    culture_id = db.Column(db.ForeignKey("culture.id", ondelete="cascade", onupdate="cascade"))
    extraction_identifier = db.Column(db.Integer, comment="An identifier to differentiate multiple extracts from the "
                                                          "ame sample on the same day. It will usually be 1, but if "
                                                          "this is the second extract done on this sample on this day, "
                                                          "it needs to be 2 (and so on).")
    extraction_machine = db.Column(db.VARCHAR(60), comment="E.g. QiaSymphony, manual")
    extraction_kit = db.Column(db.VARCHAR(60), comment="E.g. Qiasymphony Minikit")
    extraction_from = db.Column(db.VARCHAR(60), comment="E.g. plate sweep, isolate, whole sample")
    what_was_extracted = db.Column(db.VARCHAR(60), comment="E.g. DNA, RNA")
    date_extracted = db.Column(db.DateTime, comment="Date this extract was done")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    processing_institution = db.Column(db.VARCHAR(60), comment="The institution which did the DNA extraction.")
    raw_sequencing = db.relationship("RawSequencing", backref=backref("extraction", passive_deletes=True))
    tiling_pcrs = db.relationship("TilingPcr", backref=backref("extraction", passive_deletes=True))
    covid_confirmatory_pcrs = db.relationship("CovidConfirmatoryPcr", backref=backref("extraction", passive_deletes=True))
    nucleic_acid_concentration = db.Column(db.Numeric, comment="The concentration of nucleic acid in ng/ul.")
    submitter_plate_id = db.Column(db.VARCHAR(60), comment="The plate ID given by the submitter.")
    submitter_plate_well = db.Column(db.VARCHAR(60), comment="The well ID given by the submitter.")
    elution_plate_id = db.Column(db.VARCHAR(60), comment="The elution plate ID given by the lab.")
    elution_plate_well = db.Column(db.VARCHAR(60), comment="The elution well ID given by the lab.")
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"Extraction(id={self.id}, sample.id={self.sample_id}, date_extracted={self.date_extracted})"


class TilingPcr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraction_id = db.Column(db.ForeignKey("extraction.id", ondelete="cascade", onupdate="cascade"))
    number_of_cycles = db.Column(db.Integer, comment="Number of PCR cycles")
    date_pcred = db.Column(db.DateTime, comment="Date this PCR was done")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    protocol = db.Column(db.VARCHAR(60), comment="Tiling PCR protocol")
    pcr_identifier = db.Column(db.Integer, comment="Differentiates this PCR from other PCRs done on this sample on the "
                                                   "same day.")
    raw_sequencings = db.relationship("RawSequencing", backref=backref("tiling_pcr", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"TilingPcr(id={self.id}, extraction.id={self.extraction_id})"


class RawSequencing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraction_id = db.Column(db.ForeignKey("extraction.id", ondelete="cascade", onupdate="cascade"))
    raw_sequencing_batch_id = db.Column(db.ForeignKey("raw_sequencing_batch.id", ondelete="cascade", onupdate="cascade"))
    tiling_pcr_id = db.Column(db.ForeignKey("tiling_pcr.id",  ondelete="cascade", onupdate="cascade"))
    data_storage_device = db.Column(db.VARCHAR(64), comment="which machine is this data stored on?")
    readsets = db.relationship("ReadSet", backref=backref("raw_sequencing", passive_deletes=True))
    raw_sequencing_nanopore = db.relationship("RawSequencingNanopore", backref=backref("raw_sequencing", passive_deletes=True), uselist=False)
    raw_sequencing_illumina = db.relationship("RawSequencingIllumina", backref=backref("raw_sequencing", passive_deletes=True), uselist=False)
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"RawSequencing(id={self.id}, extraction.id={self.extraction_id})"


class RawSequencingNanopore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raw_sequencing_id = db.Column(db.ForeignKey("raw_sequencing.id", ondelete="cascade", onupdate="cascade"))
    path_fast5 = db.Column(db.VARCHAR(250))
    library_prep_method = db.Column(db.VARCHAR(64))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"RawSequencingNanopore(id={self.id}, path_fast5={self.path_fast5})"


class RawSequencingIllumina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raw_sequencing_id = db.Column(db.ForeignKey("raw_sequencing.id", ondelete="cascade", onupdate="cascade"))
    path_r1 = db.Column(db.VARCHAR(250))
    path_r2 = db.Column(db.VARCHAR(250))
    library_prep_method = db.Column(db.VARCHAR(64))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return f"RawSequencingIllumina(id={self.id}, path_r1={self.path_r1})"


class RawSequencingBatch(db.Model):
    """[Define model 'Batch' mapped to table 'batch']
    
    Arguments:
        db {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(50))
    date_run = db.Column(db.DATE)
    sequencing_type = db.Column(db.VARCHAR(64))
    instrument_model = db.Column(db.VARCHAR(64))
    instrument_name = db.Column(db.VARCHAR(64), comment="For MLW machines, which exact machine was it run on")
    # primer = db.Column(db.VARCHAR(100))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    sequencing_centre = db.Column(db.VARCHAR(64), comment="E.g. Sanger, CGR, MLW, etc.")
    flowcell_type = db.Column(db.VARCHAR(64))
    raw_sequencings = db.relationship("RawSequencing", backref=backref("raw_sequencing_batch", passive_deletes=True))
    batch_directory = db.Column(db.VARCHAR(128))
    readset_batches = db.relationship("ReadSetBatch", backref=backref("raw_sequencing_batch", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")

    def __repr__(self):
        return '<Batch {}>'.format(self.name)


sample_source_project = db.Table("sample_source_project",
                                  db.Column("sample_source_id", db.Integer, db.ForeignKey("sample_source.id", ondelete='cascade', onupdate="cascade"),
                                            primary_key=True),
                                  db.Column("project_id", db.Integer, db.ForeignKey("project.id", ondelete='cascade', onupdate="cascade"), primary_key=True)
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

    samples = db.relationship("Sample", backref=backref("sample_source", passive_deletes=True))
    latitude = db.Column(db.Float(), comment="Latitude of sample source if known")
    longitude = db.Column(db.Float(), comment="Longitude of sample source origin if known")
    country = db.Column(db.VARCHAR(60), comment="country of origin")
    location_first_level = db.Column(db.VARCHAR(40), comment="Highest level of organisation within country e.g. region,"
                                                             " province, state")
    location_second_level = db.Column(db.VARCHAR(50), comment="Second highest level of organisation e.g. county, "
                                                              "district Malawi), large city/metro area")
    location_third_level = db.Column(db.VARCHAR(50), comment="Third highest level of organisation e.g. district "
                                                             "(UK/VN), township (MW)")
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    # projects = db.relationship("Project", secondary="sample_source_project", backref=backref("sample_sources", passive_deletes=True))


class Project(db.Model):
    """[Define model 'project' mapped to table 'project']

    Returns:
        [type] -- [description]
    """
    id = db.Column(db.Integer, primary_key=True)
    groups_id = db.Column(db.ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"))
    project_name = db.Column(db.VARCHAR(64), comment="You can think about this as 'what study got ethics for this "
                                                     "sample to be taken'")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    project_details = db.Column(db.VARCHAR(160))
    # __table_args__ = (UniqueConstraint('project_name', 'group_name', name='_projectname_group_uc'),)
    # todo - add in a constraint somehow so that project_name is unique within group
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    sample_sources = db.relationship("SampleSource", secondary="sample_source_project", backref=backref("projects", passive_deletes=True))

    def __repr__(self):
        return f"Project(id: {self.id}, details: {self.project_name})"


class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.VARCHAR(60), comment="The name of the group running this project (again, think about"
                                                   "this in context of ethics permission).")
    institution = db.Column(db.VARCHAR(60), comment="The name of the institution where this group work.")
    pi = db.Column(db.VARCHAR(60), comment="The name of the PI of this group")
    projects = db.relationship("Project", backref=backref("groups", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")


class CovidConfirmatoryPcr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # link to extraction
    extraction_id = db.Column(db.ForeignKey("extraction.id", ondelete="cascade", onupdate="cascade"))
    ct = db.Column(db.Numeric, comment="Ct value of the confirmatory PCR")
    protocol = db.Column(db.VARCHAR(60), comment="What is the name/identifier of the assay? E.g. CDC v1")
    date_pcred = db.Column(db.DateTime, comment="Date this PCR was done")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    pcr_identifier = db.Column(db.Integer, comment="Differentiates this PCR from other PCRs done on this sample on the "
                                                   "same day.")
    notes = db.Column(db.VARCHAR(256), comment="General comments.")


class PcrResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.ForeignKey("sample.id", ondelete="cascade", onupdate="cascade"))
    pcr_result = db.Column(db.VARCHAR(60), comment="Was the test positive or negative")
    ct = db.Column(db.Numeric, comment="Was the test positive or negative")
    date_pcred = db.Column(db.DateTime, comment="Date this PCR was done")
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    institution = db.Column(db.VARCHAR(60), comment="Which institution did this PCR?")
    pcr_identifier = db.Column(db.Integer, comment="Differentiates this PCR from other PCRs done on this sample on the "
                                                   "same day.")
    pcr_assay_id = db.Column(db.ForeignKey("pcr_assay.id", ondelete="cascade", onupdate="cascade"))


class PcrAssay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assay_name = db.Column(db.VARCHAR(60), comment="What is the name/identifier of the assay? E.g. sars-cov-2 CDC v1")
    pcr_results = db.relationship("PcrResult", backref=backref("pcr_assay", passive_deletes=True))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")


class ArticCovidResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_name = db.Column(db.VARCHAR(60), comment="The sample name from the artic result output.")
    pct_N_bases = db.Column(db.Numeric, comment="Percentage N bases")
    pct_covered_bases = db.Column(db.Numeric, comment="Percentage covered bases")
    num_aligned_reads = db.Column(db.Numeric, comment="The number of aligned reads")
    workflow = db.Column(db.VARCHAR(60), comment="Workflow e.g. illumina, medaka, nanopolish")
    profile = db.Column(db.VARCHAR(60), comment="Profile e.g. docker, conda, etc")
    readset_id = db.Column(db.ForeignKey("read_set.id", ondelete="cascade", onupdate="cascade"))
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    pangolin_results = db.relationship("PangolinResult", backref=backref("artic_covid_result", passive_deletes=True))


class PangolinResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lineage = db.Column(db.VARCHAR(60), comment="The pangolin lineage")
    conflict = db.Column(db.Numeric, comment="How many other lineages could this sample feasibly be?")
    ambiguity_score = db.Column(db.Numeric, comment="the proportion of relevant sites in a sequnece which were imputed "
                                                    "to the reference values. A score of 1 indicates that no sites were"
                                                    " imputed, while a score of 0 indicates that more sites were "
                                                    "imputed than were not imputed. This score only includes sites "
                                                    "which are used by the decision tree to classify a sequence")
    scorpio_call = db.Column(db.VARCHAR(60), comment="Output of scorpio tool.")
    scorpio_support = db.Column(db.Numeric, comment="The proportion of defining variants which have the alternative "
                                                    "allele in the sequence")
    scorpio_conflict = db.Column(db.Numeric, comment="the proportion of defining variants which have the reference "
                                                     "allele in the sequence. Ambiguous/other non-ref/alt bases at each"
                                                     " of the variant positions contribute only to the denominators of"
                                                     " these scores")
    version = db.Column(db.VARCHAR(60), comment="See https://cov-lineages.org/pangolin_docs/output.html")
    pangolin_version = db.Column(db.VARCHAR(60), comment="Pangolin version")
    # todo - pangolearn version should be a date
    pangolearn_version = db.Column(db.DateTime, comment="Pangolearn version")
    pango_version = db.Column(db.VARCHAR(60), comment="The sample name from the artic result output.")
    status = db.Column(db.VARCHAR(60), comment="Pass/fail QC")
    note = db.Column(db.VARCHAR(300), comment="If any conflicts from the decision tree, this field will output the "
                                             "alternative assignments. ")
    notes = db.Column(db.VARCHAR(256), comment="General comments.")
    artic_covid_result_id = db.Column(db.ForeignKey("artic_covid_result.id", ondelete="cascade", onupdate="cascade"))

