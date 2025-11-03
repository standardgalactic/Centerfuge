module Main exposing (main)
import Browser
import Html exposing (Html, div, text)
import Json.Decode as D
import Svg exposing (..)
import Svg.Attributes as SA
import WebSocket
import Time
type alias FieldSample = { x : Int, y : Int, phi : Float, vx : Float, vy : Float, s : Float }
type alias Model = Maybe (List FieldSample)
init _ = ( Nothing, Cmd.none )
type Msg = Tick Time.Posix | ReceiveData (Result WebSocket.Error (List FieldSample))
update msg model = case msg of
	Tick _ -> (model, Cmd.none)
	ReceiveData (Ok samples) -> (Just samples, Cmd.none)
	_ -> (model, Cmd.none)
subscriptions _ = Sub.batch [ WebSocket.listen "ws://localhost:8080/ws" ReceiveData, Time.every 100 Tick ]
main = Browser.element { init = init, update = update, view = view, subscriptions = subscriptions }
view model = case model of
	Nothing -> div [] [ text "Connecting..." ]
	Just samples -> svg [ SA.width "640", SA.height "640" ] (List.map cell samples)
cell s = let c = String.fromInt (round (255 * (0.5 + s.phi / 2))) in rect [ SA.x (String.fromInt (s.x * 10)), SA.y (String.fromInt (s.y * 10)), SA.width "10", SA.height "10", SA.fill ("rgb("++c++","++c++","++c++")") ] []
