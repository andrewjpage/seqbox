from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, SampleForm, BatchForm, LocationForm, Result1Form, MykrobeForm,ProjectForm, Sample_projectForm
from app.models import User, Mykrobe, Project #, Sample_project #Sample, Batch, Location, Result1

@app.route('/')
@app.route('/index',methods=['GET', 'POST'])
@login_required
def index():
    
    """[The way Flask-Login protects a view function against anonymous users is with a decorator called @login_required. 
    When we add this decorator to a view function below the @app.route decorators from Flask, the function becomes protected and will not allow access to users that are not authenticated.  ]

    """
 
    posts = [
        {
            'author': {'username': 'Oucru'},
            'body': 'Welcome to Seqbox Platform!'
        }
        
    ]


    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():

    """[The view function creates a LoginForm object and uses it like the simple form.
    when the request is of type GET,the view function just redersz the template,
    which in turn displays the form.when the form is submitted i a POST request Flask-WTF's 
    validate_on_submit() function validates the form variables, and then attempts to log the user in.]
    
    """
    if current_user.is_authenticated:

        """[The current_user variable comes from Flask-Login and can be used  to obtain the user object that represents the client of the request. 
        The value of this variable can be a user object from the database or a special anonymous user object if the user did not log in yet.
        The is_authenticated check if the user is logged in or not and redirect the index page when user is logged in. ]
        """
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    """[summary]
    
    Returns:
        [type] -- [description]
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """[summary]
    
    Returns:
        [type] -- [description]
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        #save the model to the database
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/sample', methods=['GET', 'POST'])
def sample():

    """[summary]
    
    Returns:
        [type] -- [description]
    """
   
    form = SampleForm()
    if form.validate_on_submit():

        result1=form.result1.data
        mykrobe=form.mykrobe.data
        batch=form.batch.data
        location=form.location.data
        result1= None if result1 =='' else result1
        mykrobe= None if mykrobe == '' else mykrobe
        batch= None if batch =='' else batch
        location= None if location =='' else location

        sample = Sample(id_sample=form.id_sample.data, num_reads=form.num_reads.data,
                        date_time=form.date_time.data, organism=form.organism.data,
                        location=location, batch=batch,
                        path_r1=form.path_r1.data, path_r2=form.path_r2.data,
                        result1=result1, mykrobe=mykrobe)
        print(sample)
        #save the model to the database
        db.session.add(sample)
        db.session.commit()
        
        flash('Congratulations, you are now a registered sample!')
        return redirect(url_for('index'))
    return render_template('sample.html', title='validate', form=form)


@app.route('/list_sample', methods = ['GET', 'POST'])
def list_sample():
    """
    List all sample
    """
    if request.method == 'GET':
        samples=db.session.query(Sample).all()
        db.session.commit()
        # return render_template('query.html', samples=samples, title='list sample')
        # for sample in samples:
        #     print(sample)
        #     print (sample.id_sample,sample.num_reads,sample.date_time,sample.batch,sample.organism,sample.location,sample.path_r1,sample.path_r2,sample.result1,sample.mykrobe)
        #     flash('Sample selected successfully!')
        return render_template('query.html', samples=samples, title='list sample')
    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('sample_delete',id = id))
    

@app.route('/edit/<id>', methods = ['GET', 'POST'])
def edit(id):  

    if request.method == 'GET': 
        kwargs = {'id_sample':id}
        sample=Sample.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('sample_edit.html',
                           sample=sample)


    if request.method == 'POST':
        id_sample = request.form.get('id_sample')
        num_reads = request.form.get('num_reads')
        date_time = request.form.get('date_time')
        batch = request.form.get('batch')
        organism = request.form.get('organism')
        location= request.form.get('location')
        path_r1 = request.form.get('path_r1')
        path_r2= request.form.get('path_r2')
        result1 = request.form.get('result1')
        mykrobe = request.form.get('mykrobe')
        Sample.query.filter_by(id_sample=id_sample).update({"num_reads": num_reads,
            "date_time":date_time, "batch": batch,"organism": organism,
            "location": location,"path_r1":path_r1,"path_r2": path_r2,"result1":result1,"mykrobe":mykrobe})
        

        db.session.commit()
        flash('Sample modifited successfully!')
        return render_template('index.html')

@app.route('/sample_delete/<id>', methods=['GET', 'POST'])
def sample_delete(id):

    Sample_project.query.filter_by(id_sample=id).delete()
    Sample.query.filter_by(id_sample=id).delete()    
    db.session.commit()
    flash('Sample is deleted')
    return render_template('sample_delete.html')

@app.route('/batch', methods=['GET', 'POST'])
def batch():
    form = BatchForm()
    if form.validate_on_submit():
        batch = Batch(id_batch=form.id_batch.data, name_batch=form.name_batch.data, date_batch=form.date_batch.data, instrument=form.instrument.data, primer=form.primer.data)
        
        #save the model to the database
        db.session.add(batch)
        db.session.commit()
        
        flash('Congratulations, you are now a registered batch!')
        return redirect(url_for('index'))
    return render_template('batch.html', title='validate', form=form)

@app.route('/list_batch', methods = ['GET', 'POST'])
def list_batch():
    """
    List all batch
    """
    if request.method == 'GET':
        batches=db.session.query(Batch).all()
        db.session.commit()
        return render_template('batchQuery.html', batches=batches, title='list batch')
    # for batch in batches:
    #     print(batch)
    #     print (batch.id_batch,batch.name_batch,batch.date_batch,batch.instrument,batch.primer)
    #     flash('Batch selected successfully!')
    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('batch_edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('batch_delete',id = id))

@app.route('/batch_edit/<id>', methods = ['GET', 'POST'])
def batch_edit(id):  

    if request.method == 'GET': 
        kwargs = {'id_batch':id}
        batch=Batch.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('batch_edit.html',
                           batch=batch)

    if request.method == 'POST':
        id_batch= request.form.get('id_batch')
        name_batch = request.form.get('name_batch')
        date_batch = request.form.get('date_batch')
        instrument = request.form.get('instrument')
        primer = request.form.get('primer')
        batch=Batch.query.filter_by(id_batch=id_batch).update({"name_batch": name_batch,"date_batch": date_batch,
            "instrument": instrument,"primer": primer})
        db.session.commit()
        flash('Batch modifited successfully!')
        return render_template('index.html')
   
@app.route('/batch_delete/<id>', methods=['GET', 'POST'])
def batch_delete(id):

    Batch.query.filter_by(id_batch=id).delete()    
    db.session.commit()
    flash('Batch is deleted')
    return render_template('batch_delete.html') 

@app.route('/location', methods=['GET', 'POST'])
def location():
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(id_location=form.id_location.data, continent=form.continent.data, country=form.country.data, province=form.province.data, city=form.city.data)
        
        #save the model to the database
        db.session.add(location)
        db.session.commit()
        
        flash('Congratulations, you are now a registered location!')
        return redirect(url_for('index'))
    return render_template('location.html', title='validate', form=form)

@app.route('/list_location', methods = ['GET', 'POST'])
def list_location():
    """
    List all location
    """
    if request.method == 'GET':
        locations=db.session.query(Location).all()
        db.session.commit()
        return render_template('locationQuery.html', locations=locations, title='list location')

    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('location_edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('location_delete',id = id))

@app.route('/location_edit/<id>', methods = ['GET', 'POST'])
def location_edit(id):  

    if request.method == 'GET': 
        kwargs = {'id_location':id}
        location=Location.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('location_edit.html',
                           location=location)

    if request.method == 'POST':
        id_location = request.form.get('id_location')
        continent = request.form.get('continent')
        country = request.form.get('country')
        province = request.form.get('province')
        city = request.form.get('city')
        location=Location.query.filter_by(id_location=id_location).update({"continent":continent, 
            "country":country, "province":province, 
            "city":city})
        db.session.commit()
        flash('Location modifited successfully!')
        return render_template('index.html')
   

@app.route('/location_delete/<id>', methods=['GET', 'POST'])
def location_delete(id):

    Location.query.filter_by(id_location=id).delete()    
    db.session.commit()
    flash('Location is deleted')
    return render_template('location_delete.html')

@app.route('/result1', methods=['GET', 'POST'])
def result1():
    form = Result1Form()
    if form.validate_on_submit():
        result1 = Result1(id_result1=form.id_result1.data, qc=form.qc.data, ql=form.ql.data, description=form.description.data, snapper_variants=form.snapper_variants.data, snapper_ignored=form.snapper_ignored.data, num_heterozygous=form.num_heterozygous.data, mean_depth=form.mean_depth.data, coverage=form.coverage.data)
        
        #save the model to the database
        db.session.add(result1)
        db.session.commit()
        
        flash('Congratulations, you are now a registered result1!')
        return redirect(url_for('index'))
    return render_template('result1.html', title='validate', form=form)
@app.route('/list_result1', methods = ['GET', 'POST'])
def list_result1():
    """
    List all result1
    """
    if request.method == 'GET':
        result1s=db.session.query(Result1).all()
        db.session.commit()
        return render_template('result1Query.html', result1s=result1s, title='list result1')

    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('result1_edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('result1_delete',id = id))
    

@app.route('/result1_edit/<id>', methods = ['GET', 'POST'])
def result1_edit(id):  

    if request.method == 'GET': 
        kwargs = {'id_result1':id}
        result1=Result1.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('result1_edit.html',
                           result1=result1)

    if request.method == 'POST':
        id_result1 = request.form.get('id_result1')
        qc = request.form.get('qc')
        ql = request.form.get('ql')
        description = request.form.get('description')
        snapper_variants = request.form.get('snapper_variants')
        snapper_ignored = request.form.get('snapper_ignored')
        num_heterozygous = request.form.get('num_heterozygous')
        mean_depth = request.form.get('mean_depth')
        coverage = request.form.get('coverage')
        
        result1=Result1.query.filter_by(id_result1=id_result1).update({"qc": qc,"ql": ql,"description": description,
            "snapper_variants": snapper_variants,
            "snapper_ignored": snapper_ignored,"num_heterozygous": num_heterozygous,
            "mean_depth": mean_depth,"coverage": coverage})
        db.session.commit()
        flash('Result1 modifited successfully!')
        return render_template('index.html')
    

@app.route('/result1_delete/<id>', methods=['GET', 'POST'])
def result1_delete(id):

    Result1.query.filter_by(id_result1=id).delete()    
    db.session.commit()
    flash('Result1 is deleted')
    return render_template('result1_delete.html')

@app.route('/mykrobe', methods=['GET', 'POST'])
def mykrobe():
    form = MykrobeForm()
    if form.validate_on_submit():
        mykrobe = Mykrobe(id_mykrobe=form.id_mykrobe.data, mykrobe_version=form.mykrobe_version.data, phylo_grp=form.phylo_grp.data, phylo_grp_covg=form.phylo_grp_covg.data, phylo_grp_depth=form.phylo_grp_depth.data, species=form.species.data, species_covg=form.species_covg.data, species_depth=form.species_depth.data, lineage=form.lineage.data, lineage_covg=form.lineage_covg.data, lineage_depth=form.lineage_depth.data, susceptibility=form.susceptibility.data, variants=form.variants.data, genes=form.genes.data, drug=form.drug.data)
        
        #save the model to the database
        db.session.add(mykrobe)
        db.session.commit()
        
        flash('Congratulations, you are now a registered mykrobe!')
        return redirect(url_for('index'))
    return render_template('mykrobe.html', title='validate', form=form)

@app.route('/list_mykrobe', methods = ['GET', 'POST'])
def list_mykrobe():
    """
    List all mykrobe
    """
    if request.method == 'GET':
        mykrobes=db.session.query(Mykrobe).all()
        db.session.commit()
        return render_template('mykrobeQuery.html', mykrobes=mykrobes, title='list mykrobe')

    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('mykrobe_edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('mykrobe_delete',id = id))
    

@app.route('/mykrobe_edit/<id>', methods = ['GET', 'POST'])
def mykrobe_edit(id):  

    if request.method == 'GET': 
        kwargs = {'id_mykrobe':id}
        mykrobe=Mykrobe.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('mykrobe_edit.html',
                           mykrobe=mykrobe)

    if request.method == 'POST':
        id_mykrobe = request.form.get('id_mykrobe')
        mykrobe_version= request.form.get('mykrobe_version')
        phylo_grp = request.form.get('phylo_grp')
        phylo_grp_covg= request.form.get('phylo_grp_covg')
        phylo_grp_depth = request.form.get('phylo_grp_depth')
        species= request.form.get('species')
        species_covg = request.form.get('species_covg')
        species_depth = request.form.get('species_depth')
        lineage = request.form.get('lineage')
        lineage_covg = request.form.get('lineage_covg')
        lineage_depth = request.form.get('lineage_depth')
        susceptibility = request.form.get('susceptibility')
        variants = request.form.get('variants')
        genes = request.form.get('genes')
        drug = request.form.get('drug')
          
        
        mykrobe=Mykrobe.query.filter_by(id_mykrobe=id_mykrobe).update({"mykrobe_version":mykrobe_version, "phylo_grp":phylo_grp,
            "phylo_grp_covg":phylo_grp_covg,"phylo_grp_depth":phylo_grp_depth,
            "species":species,"species_covg":species_covg,
            "species_depth":species_depth,"lineage":lineage,
            "lineage_covg":lineage_covg,"lineage_depth":lineage_depth,
            "susceptibility":susceptibility,"variants":variants,
            "genes":genes,"drug":drug})
        db.session.commit()
        flash('Mykrobe modifited successfully!')
        return render_template('index.html')
    

@app.route('/mykrobe_delete/<id>', methods=['GET', 'POST'])
def mykrobe_delete(id):

    Mykrobe.query.filter_by(id_mykrobe=id).delete()
    db.session.commit()
    flash('Mykrobe is deleted')
    return render_template('mykrobe_delete.html')

@app.route('/project', methods=['GET', 'POST'])
def project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(id_project=form.id_project.data, date_project=form.date_project.data, result_project=form.result_project.data)
        
        #save the model to the database
        db.session.add(project)
        db.session.commit()

        flash('Congratulations, you are now a registered project!')
        return redirect(url_for('index'))
    return render_template('project.html', title='validate', form=form)

@app.route('/list_project', methods = ['GET', 'POST'])
def list_project():
    """
    List all project
    """
    if request.method == 'GET':
        projects=db.session.query(Project).all()
        db.session.commit()
        return render_template('projectQuery.html', projects=projects, title='list project')

    if request.method == 'POST':
        try: 
            id = request.form['modify']
            return redirect(url_for('project_edit', id = id))
        except:
            id = request.form['delete']
            return redirect(url_for('project_delete',id = id))
    

@app.route('/project_edit/<id>', methods = ['GET', 'POST'])
def project_edit(id):

    if request.method == 'GET': 
        kwargs = {'id_project':id}
        project=Project.query.filter_by(**kwargs).first()
        db.session.commit()
        return render_template('project_edit.html',
                           project=project)

    if request.method == 'POST':
        id_project = request.form.get('id_project')
        date_project= request.form.get('date_project')
        result_project = request.form.get('result_project')
       
        project=Project.query.filter_by(id_project=id_project).update({"id_project":id_project,"date_project":date_project,"result_project":result_project})
        db.session.commit()
        flash('Project modifited successfully!')
        return render_template('index.html')
    

@app.route('/project_delete/<id>', methods=['GET', 'POST'])
def project_delete(id):

    Project.query.filter_by(id_project=id).delete()
    db.session.commit()
    flash('Project is deleted')
    return render_template('project_delete.html')

@app.route('/sample_project', methods=['GET', 'POST'])
def sample_project():
    form = Sample_projectForm()
    if form.validate_on_submit():
        sample_project = Sample_project(id_sample=form.id_sample.data,id_project=form.id_project.data)
        
        #save the model to the database
        db.session.add(sample_project)
        db.session.commit()
        
        flash('Congratulations, you are now a registered sample_project!')
        return redirect(url_for('index'))
    return render_template('sample_project.html', title='validate', form=form)