package api
type FieldSample struct {
	X, Y   int     `json:"x"`
	Phi    float64 `json:"phi"`
	Vx, Vy float64 `json:"vx","vy"`
	S      float64 `json:"s"`
}
type FieldState struct {
	Width, Height int           `json:"width","height"`
	Samples       []FieldSample `json:"samples"`
}
func NewFieldState(w, h int) FieldState {
	s := make([]FieldSample, 0, w*h)
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			s = append(s, FieldSample{X: x, Y: y})
		}
	}
	return FieldState{Width: w, Height: h, Samples: s}
}
