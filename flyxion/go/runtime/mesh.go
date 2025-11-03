package runtime
type Tile struct{ X0, Y0, X1, Y1 int }
func Partition(width, height, tilesX, tilesY int) []Tile {
	if tilesX < 1 { tilesX = 1 }
	if tilesY < 1 { tilesY = 1 }
	var out []Tile
	wStep := (width + tilesX - 1) / tilesX
	hStep := (height + tilesY - 1) / tilesY
	for ty := 0; ty < tilesY; ty++ {
		for tx := 0; tx < tilesX; tx++ {
			x0, y0 := tx*wStep, ty*hStep
			x1, y1 := min((tx+1)*wStep, width), min((ty+1)*hStep, height)
			out = append(out, Tile{x0, y0, x1, y1})
		}
	}
	return out
}
func min(a, b int) int { if a < b { return a }; return b }
