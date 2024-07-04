import os
import wave

input_path = os.path.join(os.getcwd(), "16000_pcm_speeches", "audio")
output_path = os.path.join(os.getcwd(), "16000_pcm_speeches_MODIFIED", "audio")

input_paths = [
    os.path.join(input_path, "Benjamin_Netanyau"),
    os.path.join(input_path, "Jens_Stoltenberg"),
    os.path.join(input_path, "Julia_Gillard"),
    os.path.join(input_path, "Magaret_Tarcher"),
    os.path.join(input_path, "Nelson_Mandela"),
]
output_paths = [
    os.path.join(output_path, "Benjamin_Netanyau"),
    os.path.join(output_path, "Jens_Stoltenberg"),
    os.path.join(output_path, "Julia_Gillard"),
    os.path.join(output_path, "Magaret_Tarcher"),
    os.path.join(output_path, "Nelson_Mandela"),
]

for i in range(len(input_paths)):
    print(f"Combining files in {input_paths[i]}...")

    for j in range(300):
        infiles = [
            os.path.join(input_paths[i], f"{j * 5 + 0}.wav"),
            os.path.join(input_paths[i], f"{j * 5 + 1}.wav"),
            os.path.join(input_paths[i], f"{j * 5 + 2}.wav"),
            os.path.join(input_paths[i], f"{j * 5 + 3}.wav"),
            os.path.join(input_paths[i], f"{j * 5 + 4}.wav"),
        ]
        outfile = os.path.join(output_paths[i], f"{j}.wav")

        data=[]
        for infile in infiles:
            w = wave.open(infile, 'rb')
            data.append( [w.getparams(), w.readframes(w.getnframes())] )
            w.close()
            
        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        for k in range(len(data)):
            output.writeframes(data[k][1])
        output.close()

        print(f"File {outfile} created.")

    print("Files combined successfully.")