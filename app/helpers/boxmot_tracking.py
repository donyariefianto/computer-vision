import asyncio
from datetime import datetime, timezone
import cv2
import numpy as np
from boxmot import BotSort
import torch
from pathlib import Path
from app.helpers.mongodb_manager import MongoDBManager
from app.helpers.websocket_manager import websocket_manager

class BoxmotTracking:
    def get_max_confidence(data):
        return max(data, key=lambda x: x.get("confidence", float('-inf')))
    
    async def report_crossing(data):
        high_confidence = BoxmotTracking.get_max_confidence(data["history"])
        data_recent = {
            "device_name":data["device_name"],
            "device_id":data["device_id"],
            "timestamp":data["timestamp"],
            "direction":data["direction"],
            "label":high_confidence["label"],
            "confidence":high_confidence["confidence"],
            "frame_id":high_confidence["frame_id"]
        }
        print(data)
        await MongoDBManager().insert(data)
        await websocket_manager.send_personal_message(data_recent, "recent-captured-data")
        await asyncio.sleep(0)
    
    def process_detections(frame, model, confidence):
        detections = []
        results = model.predict(frame, conf=confidence, verbose=False)  # Set confidence threshold
        boxes = results[0].boxes.xyxy.cpu().numpy()  # Bounding boxes [x1, y1, x2, y2]
        confidences = results[0].boxes.conf.cpu().numpy()  # Confidence scores
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)  # Class IDs

        for box, confiden, class_id in zip(boxes, confidences, class_ids):
            if class_id in [2, 3, 4, 5, 6, 7, 8]:
                x1, y1, x2, y2 = box
                w, h = x2 - x1, y2 - y1
                detections.append([x1, y1, x2, y2, confiden, class_id])
        return np.array(detections)
    
    async def update_track_crossing(confidence,class_id,track_id,x1, y1, x2, y2,cx, cy,vertical_line_points, horizontal_line_points,track_histories,frame,crossed,model,device_name,device_id):
        vertical_x1, vertical_y1 = vertical_line_points[0]
        vertical_x2, vertical_y2 = vertical_line_points[1]

        horizontal_x1, horizontal_y1 = horizontal_line_points[0]
        horizontal_x2, horizontal_y2 = horizontal_line_points[1]

        # Pastikan track_histories memiliki entri untuk track_id
        if (track_id not in track_histories) and (track_id not in crossed):
            track_histories[track_id] = []

        # Ambil posisi sebelumnya dari track_histories jika ada
        if track_histories[track_id]:
            previous_cx, previous_cy = track_histories[track_id][-1]["centroid"]
        else:
            previous_cx, previous_cy = cx, cy  # Jika belum ada, gunakan posisi saat ini

        # Append history data yang dipastikan belum melintas jika sudah maka akan di lewati saja
        if track_id not in crossed:
            track_histories[track_id].append({
                "class_id":class_id,
                "confidence":confidence,
                "bounding_box": (x1, y1, x2, y2),
                "centroid": (cx, cy),
                "label":model.names[int(class_id)],
                "frame_id":frame
            })
        
        # Check crossing for horizontal line
        if previous_cy < horizontal_y1 <= cy:
            await BoxmotTracking.report_crossing({
                "device_name":device_name,
                "device_id":device_id,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),  # GMT+0 Timestamp
                "direction":"crossed UP to DOWN.",
                "history":track_histories[track_id]
            })
            del track_histories[track_id]
            crossed.add(track_id)
            # print(f"Track ID {track_id} crossed UP to DOWN.")
        elif previous_cy > horizontal_y1 >= cy:
            await BoxmotTracking.report_crossing({
                "device_name":device_name,
                "device_id":device_id,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),  # GMT+0 Timestamp
                "direction":"crossed DOWN to UP.",
                "history":track_histories[track_id]
            })
            del track_histories[track_id]
            crossed.add(track_id)
            # print(f"Track ID {track_id} crossed DOWN to UP.")

        # Check crossing for vertical line
        if previous_cx < vertical_x1 <= cx:
            await BoxmotTracking.report_crossing({
                "device_name":device_name,
                "device_id":device_id,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),  # GMT+0 Timestamp
                "direction":"crossed LEFT to RIGHT.",
                "history":track_histories[track_id]
            })
            del track_histories[track_id]
            crossed.add(track_id)
            # print(f"Track ID {track_id} crossed LEFT to RIGHT.")
        elif previous_cx > vertical_x1 >= cx:
            await BoxmotTracking.report_crossing({
                "device_name":device_name,
                "device_id":device_id,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),  # GMT+0 Timestamp
                "direction":"crossed RIGHT to LEFT.",
                "history":track_histories[track_id]
            })
            del track_histories[track_id]
            crossed.add(track_id)
            # print(f"Track ID {track_id} crossed RIGHT to LEFT.")

    def initial_tracker():
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return BotSort(reid_weights=Path('osnet_x0_25_msmt17.pt'), device=device, half=False)
    
    def draw_virtual_lines(frame, vertical_line_points, horizontal_line_points):
        """Draw virtual lines for multi-directional crossing."""
        line_color = (0, 0, 255)  # Red line
        # Draw vertical line
        cv2.line(frame, vertical_line_points[0], vertical_line_points[1], line_color, 2)
        # Draw horizontal line
        cv2.line(frame, horizontal_line_points[0], horizontal_line_points[1], line_color, 2)