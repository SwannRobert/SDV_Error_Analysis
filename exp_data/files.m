clear
clc

% Generate files U_mean_1.txt to U_mean_6.txt

for X = 1:6
    
    filename = sprintf('angle_low_%d.txt', X);
    
    % Create empty txt file
    fclose(fopen(filename, 'w'));
    
end

disp('Files created successfully.')