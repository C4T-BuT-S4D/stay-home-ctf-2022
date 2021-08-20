from flask import Flask, request, jsonify

app = Flask(__name__)

notes = set()

@app.route('/put_note', methods=['POST'])
def put_note():
    note = request.json
    if type(note) != dict or "name" not in note or "value" not in note:
        return jsonify({"ok": False, "error": "invalid note"})

    name = note["name"]
    value = note["value"]

    notes.add(name)

    with open(f"notes/{name}", "w") as f:
        f.write(value)

    return jsonify({"ok": True})

@app.route('/get_note', methods=['POST'])
def get_note():
    note = request.json
    if type(note) != dict or "name" not in note:
        return jsonify({"ok": False, "error": "invalid note"})

    name = note["name"]
    if name not in notes:
        return jsonify({"ok": False, "error": "no such note"})

    with open(f"notes/{name}", "r") as f:
        value = f.read()

    return jsonify({"ok": True, "note": value})

