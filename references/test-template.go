package example

import (
	"errors"
	"testing"
)

// Template: replace TypeUnderTest / FunctionUnderTest / fields with the real
// signature. Keep the structure — table + t.Run + t.Parallel — as-is.

func TestFunctionUnderTest(t *testing.T) {
	tests := []struct {
		name    string      // describe the SCENARIO, not just the input
		input   InputType   // whatever FunctionUnderTest takes
		want    OutputType  // the independently-derived expected result
		wantErr error       // nil if no error expected
	}{
		{
			name:    "happy path: <describe the normal case>",
			input:   InputType{ /* ... */ },
			want:    OutputType{ /* ... */ }, // derive this by hand; add a comment showing how
			wantErr: nil,
		},
		{
			name:    "boundary: exactly at the threshold",
			input:   InputType{ /* value == the branch condition's boundary */ },
			want:    OutputType{ /* ... */ },
			wantErr: nil,
		},
		{
			name:    "edge: zero/empty input",
			input:   InputType{},
			want:    OutputType{},
			wantErr: nil,
		},
		{
			name:    "error path: <describe what triggers the error>",
			input:   InputType{ /* invalid value */ },
			want:    OutputType{},
			wantErr: ErrSomeSentinelError,
		},
		// Add one case per branch in the function under test.
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got, err := FunctionUnderTest(tt.input)

			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("FunctionUnderTest(%v) error = %v, want %v", tt.input, err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("FunctionUnderTest(%v) = %v, want %v", tt.input, got, tt.want)
			}
		})
	}
}
