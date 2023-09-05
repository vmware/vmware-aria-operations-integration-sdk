#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os


def build_template(path: str, root_directory: str) -> None:
    with open(os.path.join(path, root_directory, "Adapter.java"), "w") as collector:
        collector.write(
            """
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.*;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class Adapter {

    public static void main(String[] args) {
        // Check if there are enough command line arguments
//        ObjectMapper mapper = new ObjectMapper();
//        ObjectNode rootNode = mapper.createObjectNode();
//
//        rootNode.put("name", "John");
//        rootNode.put("age", 30);
//
//        String jsonString = rootNode.toString(); // Convert the JSON object to a string
//        System.out.println(jsonString);

        if (args.length != 3) {
            System.out.println("Please provide 3 command line arguments.");
            System.out.println(Arrays.toString(args));
            return;
        }


        // Read the command
        String command = args[0];
        String response = "";
        switch (command){
            case "test":
                System.out.println("testing");
                response = test(getContent(args[1]));
                break;
            case "collect":
                System.out.println("collecting");
                break;
            case "endpoint":
                System.out.println("gathering endpoints");
                break;
            case "adapter_definition":
                System.out.println("gathering adapter definitions");
                break;
            default:
                System.out.println("Invalid command. Allowed values: test, endpoint, collect, adapter.");
                System.out.println(Arrays.toString(args));
        }


        // Process the input pipe
        try {
            // Write an empty JSON to the output pipe
            FileOutputStream outPipe = new FileOutputStream(args[2]);
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(outPipe));
            writer.write(response);
            writer.close();
        } catch (IOException e) {
            System.err.println("Error reading/writing to the pipes: " + e.getMessage());
        }
    }

    private static JsonNode getContent(String pipe) {
        JsonNode map = null;

        try {
            FileInputStream inPipe = new FileInputStream(pipe);
            ObjectMapper mapper = new ObjectMapper();

            map = mapper.readTree(inPipe);

        } catch (IOException e){
                System.err.println("Error reading/writing to the pipes: " + e.getMessage());
                e.printStackTrace();
        }
        return map;
    }

    private static String test(JsonNode adapterDefinition) {
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode rootNode = mapper.createObjectNode();

        if (adapterDefinition.path("adapter_key")
                .path("identifiers")
                .get(0)
                .path("value")
                .asText()
                .equals("bad")){
            rootNode.put("errorMessage", "Oh no something went horribly wrong!");
        }

        return rootNode.toString();
    }
}

"""
        )


def compile(source_directory: str, output_directory: str) -> None:
    # compile class
    os.system(f"javac -d {output_directory} {source_directory}/Adapter.java")
