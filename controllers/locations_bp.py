from flask import Blueprint, render_template, request, redirect, url_for, abort
from repository.locations_repository import LocationsRepository
from repository.objects_repository import ObjectsRepository
from repository.constituent_repository import ConstituentRepository
from repository.locations_repository import Location
from flask_paginate import Pagination, get_page_args
from models.object import ObjectDTO

def locations_bp(connection):
    locations = Blueprint(
        'locations',
        __name__,
        template_folder='../templates/locations',
        static_folder='static/',
        url_prefix="/locations"
    )

    repository = LocationsRepository(connection=connection)
    objects_repository = ObjectsRepository(connection=connection)
    constituents_repository = ConstituentRepository(connection=connection)

    @locations.route('/', methods=['GET', 'POST'])
    def locations_page():      
        search = request.args.get("locations-search")
        filter = {"public": "", "type": ""}
        filter["public"] = request.form.getlist("public")
        filter["type"] = request.form.getlist("locationtype")
        page, per_page, offset = get_page_args(
                page_parameter="page", per_page_parameter="per_page"
            )
        per_page = 25
        all_locations = repository.get_locations(search, filter)
        locations = repository.get_locations(search, filter, offset=offset, limit=per_page)
        total = len(all_locations)
        buildings = repository.get_buildings()

        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap4'
        )
        return render_template("locations.html", locations=locations, buildings=buildings, pagination=pagination)
    
    @locations.route('building/<building_id>', methods=['GET', 'POST'])
    def building_page(building_id): 
        if request.method == "POST":           
            if "delete" in request.form:
                building = repository.get_location(building_id)
                repository.delete_location(building)
                return redirect(url_for("locations.locations_page"))
            if "edit" in request.form:
                return redirect(url_for('locations.building_edit_page', building_id=building_id))
            if "addFloor" in request.form:
                return redirect(url_for('locations.floor_add_page', building_id=building_id))
        else:
            building = repository.get_location(building_id)
            floors = repository.get_floors(building_id)
            page, per_page, offset = get_page_args(
                page_parameter="page", per_page_parameter="per_page"
            )
            per_page = 25
            all_objects = repository.get_all_objects(building_id)
            total = len(all_objects)
            objects = all_objects[offset:(offset+per_page)]
            pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap4'
            )
            DTOobjects = [objects_repository.get_object_by_objectid(objectid[0]) for objectid in objects]
            
            return render_template("building.html", building = building, floors = floors, objects = DTOobjects, pagination=pagination)
    
    @locations.route('/new_building', methods=['GET', 'POST'])
    def building_add_page():
        if request.method == "GET":
            values = {"name": "", "isPublic": ""}
            return render_template("building_edit.html", values = values)
        if 'save' in request.form:
            valid = validate_form(request.form, None)
            if not valid:
                return render_template("building_edit.html", values = request.form)
            building_name = request.form["name"]
            building_isPublic = request.form["isPublic"]
            building = Location(building_name, "building", building_isPublic)
            building_id = repository.add_location(building)          
            return redirect(url_for("locations.building_page", building_id = building_id))
        else:
            return redirect(url_for("locations.locations_page"))
    
    @locations.route('/<building_id>/edit', methods=['GET', 'POST'])
    def building_edit_page(building_id):
        if request.method == "GET":
            building = repository.get_location(building_id)
            building_isPublic = building.isPublic
            building_floors = repository.get_floors(building_id)
            values = {"name": building.name, "isPublic": building_isPublic}
            return render_template("building_edit.html", values = values)
        if 'save' in request.form:
            building_name = request.form["name"]
            building_isPublic = request.form["isPublic"]
            building = Location(building_name, "building", building_isPublic, key = building_id)
            repository.update_location(building)
            return redirect(url_for("locations.building_page", building_id=building_id))
        else:
            return redirect(url_for("locations.building_page", building_id=building_id  ))

    @locations.route('floor/<floor_id>', methods=['GET', 'POST'])
    def floor_page(floor_id): 
        if request.method == "POST":           
            if "delete" in request.form:
                floor = repository.get_location(floor_id)
                repository.delete_location(floor)
                return redirect(url_for("locations.locations_page"))
            if "edit" in request.form:
                return redirect(url_for('locations.floor_edit_page', floor_id=floor_id))
            if "addRoom" in request.form:
                return redirect(url_for('locations.room_add_page', floor_id = floor_id))
        else:
            
            rooms = repository.get_rooms(floor_id)
            floor = repository.get_location(floor_id)
            page, per_page, offset = get_page_args(
                page_parameter="page", per_page_parameter="per_page"
            )
            per_page = 25
            all_objects = repository.get_all_objects(floor_id)
            total = len(all_objects)
            objects = all_objects[offset:(offset+per_page)]
            pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap4'
            )
            DTOobjects = [objects_repository.get_object_by_objectid(objectid[0]) for objectid in objects]
            map_image = repository.get_map_image(floor_id)
            if map_image:
                return render_template("floor.html", rooms=rooms, map_image=map_image[0], floor=floor, objects=DTOobjects, pagination=pagination)
            else:
                return render_template("floor.html", rooms=rooms, map_image=None, floor=floor, objects=DTOobjects, pagination=pagination)
    @locations.route('/<building_id>/new_floor', methods=['GET', 'POST'])
    def floor_add_page(building_id): 
        if request.method == "GET":
            values = {"name": "", "isPublic": ""}
            return render_template("floor_edit.html", values = values)
        if 'save' in request.form:
            valid = validate_form(request.form, building_id)
            if not valid:
                return render_template("floor_edit.html", values = request.form)
            floor_name = request.form["name"]
            floor_isPublic = request.form["isPublic"]
            floor = Location(floor_name, "floor", floor_isPublic, building_id)
            repository.add_location(floor)       
            return redirect(url_for("locations.building_page", building_id=building_id))
        else:
            return redirect(url_for("locations.building_page", building_id=building_id))
        

    @locations.route('floor/<floor_id>/edit', methods=['GET', 'POST'])
    def floor_edit_page(floor_id):
        floor = repository.get_location(floor_id)
        if request.method == "GET":
            if floor is None:
                abort(404)
            floor_isPublic = floor.isPublic
            floor_rooms = repository.get_rooms(floor_id)
            values = {"name": floor.name, "isPublic": floor_isPublic}
            return render_template("floor_edit.html", values = values)
        if 'save' in request.form:
            floor_name = request.form["name"]
            floor_isPublic = request.form["isPublic"]
            updated_floor = Location(floor_name, "floor", floor_isPublic, floor.partof, floor_id)
            repository.update_location(updated_floor)
            return redirect(url_for("locations.floor_page", floor_id=floor_id))
        else:
            return redirect(url_for("locations.floor_page", floor_id=floor_id))
    
    @locations.route('room/<room_id>', methods=['GET', 'POST'])
    def room_page(room_id):  
        room = repository.get_location(room_id)     
        if request.method == "POST":       
            if "delete" in request.form:
                repository.delete_location(room)       
                return redirect(url_for("locations.floor_page", floor_id=room.partof))
            if "edit" in request.form:
                return redirect(url_for('locations.room_edit_page', room_id=room_id))
        else:
            objects = repository.get_objects(room_id)
            DTOobjects = [objects_repository.get_object_by_objectid(objectid[0]) for objectid in objects]
            return render_template("room.html", objects=DTOobjects, room=room)

    @locations.route('/<floor_id>/new_room', methods=['GET', 'POST'])
    def room_add_page(floor_id): 
        if request.method == "GET":
            values = {"name": "", "isPublic": "", "objects": ""}
            return render_template("room_edit.html", values = values)
        if 'save' in request.form:
            valid = validate_form(request.form, floor_id)
            if not valid:
                return render_template("room_edit.html", values = request.form)
            room_name = request.form["name"]
            room_isPublic = request.form["isPublic"]
            room_objects = request.form.getlist('objects[]')
            room = Location(room_name, "room", room_isPublic, floor_id)
            room_key = repository.add_location(room)
            room.key = room_key
            room.path = repository.get_path(room.key)
            repository.add_locationid(room)
            for object_id in room_objects:
                repository.add_object(object_id, room_key)   
            return redirect(url_for("locations.room_page", room_id=room.key))
        else:
            return redirect(url_for("locations.floor_page", floor_id=floor_id))
        
    @locations.route('room/<room_id>/edit', methods=['GET', 'POST'])
    def room_edit_page(room_id):
        room = repository.get_location(room_id)
        if request.method == "GET":
            room_isPublic = room.isPublic
            room_objects = repository.get_objects(room_id)
            values = {"name": room.name, "isPublic": room_isPublic, "objects": room_objects}
            return render_template("room_edit.html", values = values)
        if 'save' in request.form:
            room_name = request.form["name"]
            room_isPublic = request.form["isPublic"]
            room_objects = request.form.getlist('objects[]')
            removed_objects = request.form.getlist('removed_objects[]')
            for object_id in removed_objects:
                repository.remove_object(object_id)
            updated_room = Location(room_name, "room", room_isPublic, room.partof, room_id, repository.get_path(room.key))
            repository.update_location(updated_room)
            repository.update_locationid(updated_room)
            for object_id in room_objects:
                repository.add_object(object_id, room_id)
            return redirect(url_for("locations.room_page", room_id=room_id))
        else:
            return redirect(url_for("locations.room_page", room_id=room_id))
    
    def validate_form(form, locationkey):
        form.data = {}
        form.errors = {}

        form_name = form.get("name", "").strip()
        if len(form_name) == 0:
            form.errors["name"] = "Name can not be blank"
        elif not repository.is_name_unique(form_name, locationkey):
            form.errors["name"] = "Name already exists"
        else:
            form.data["name"] = form_name       
        
        form_public = form.get("isPublic")
        location = repository.get_location(locationkey)
        if location and location.isPublic == 0 and form_public == "1":
            form.errors["isPublic"] = location.name + " is not public!"
        else:
            form.data["isPublic"] = form_public

        return len(form.errors) == 0 
    return locations
