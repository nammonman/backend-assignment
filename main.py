from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel

DATABASE_NAME = "exceed12"
COLLECTION_NAME = "restaurant"
MONGO_DB_URL = "mongodb://exceed12:q7MRP7qp@mongo.exceed19.online:8443/?authMechanism=DEFAULT"


class Reservation(BaseModel):
    name: str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query = {"room_id": room_id,
             "$or":
                 [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                  {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                  {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
             }

    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name: str):
    ans = list(collection.find({"name": name}))
    if not len(ans) > 0:
        raise HTTPException(status_code=400, detail="Reservation can not be found")
    return {"name":name, "start_date": ans[0]["start_date"].strftime("%Y-%m-%d") , "end_date": ans[0]["end_date"].strftime("%Y-%m-%d") , "room_id": ans[0]["room_id"]}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    ans = list(collection.find({"room_id": room_id}))
    if not len(ans) > 0:
        raise HTTPException(status_code=400, detail="Reservation can not be found")
    return {"name":ans[0]["name"], "start_date": ans[0]["start_date"].strftime("%Y-%m-%d") , "end_date": ans[0]["end_date"].strftime("%Y-%m-%d") , "room_id": room_id}

@app.post("/reservation")
def reserve(reservation: Reservation):
    start_date = reservation.start_date.strftime("%Y-%m-%d")
    end_date = reservation.end_date.strftime("%Y-%m-%d")
    room_id = reservation.room_id
    if (start_date > end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    if (room_id < 1 or room_id > 10):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    if not room_avaliable(room_id, start_date, end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    query = {"name": str(reservation.name),
    "start_date": start_date,
    "end_date": end_date,
    "room_id": int(reservation.room_id)}
    collection.update_one(query,{f"$set":query},upsert=True)
    return {
        "name": reservation.name,
        "start_date": start_date,
        "end_date": end_date,
        "room_id": room_id
    }

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    start_date = reservation.start_date.strftime("%Y-%m-%d")
    end_date = reservation.end_date.strftime("%Y-%m-%d")
    room_id = reservation.room_id
    if (start_date > end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be updated")
    if (room_id < 1 or room_id > 10):
        raise HTTPException(status_code=400, detail="Reservation can not be updated")
    if room_avaliable(room_id,start_date,end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be updated")
    filter = {"name":reservation.name, "room_id":reservation.room_id}
    collection.update_one(filter, {"$set":{"start_date": new_start_date, "end_date": new_end_date}})
    return {
        "name": reservation.name,
        "start_date": start_date,
        "end_date": end_date,
        "room_id": room_id
    }

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    room_id = reservation.room_id
    if (room_id < 1 or room_id > 10):
        raise HTTPException(status_code=400, detail="Reservation can not be removed")
    if room_avaliable(room_id, reservation.start_date.strftime("%Y-%m-%d"), reservation.end_date.strftime("%Y-%m-%d")):
        raise HTTPException(status_code=400, detail="Reservation can not be removed")
    filter = {"name": reservation.name, "room_id": reservation.room_id}
    collection.delete_one(filter)
    return {"name": reservation.name, "start_date":reservation.start_date.strftime("%Y-%m-%d"),
            "end_date": reservation.end_date.strftime("%Y-%m-%d"), "room_id": room_id}
