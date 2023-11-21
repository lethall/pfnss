import QtQuick

Rectangle {
    id: main
    width: 400
    height: 200
    color: "blue"

    Text {
        text: "Hello World from Python!"
        color: "white"
        anchors.centerIn: main
    }
}