import csv, re, os

# Results with hardware that was available earlier are not part of the data
MIN_HARDWARE_AVAILABILITY_YEAR = 2018

header = [

'Result_ID',

'Test_Sponsor', 'SPEC_License', 'Test_Method', 'Tested_By', 'Test_Location',
'Test_Date', 'Hardware_Availability', 'Software_Availability', 'Publication',
'System_Source', 'System_Designation', 'Power_Provisioning',

'100_ActualLoad', '100_ssj_ops', '100_AvgPower', '100_PerfPowerRatio',
'90_ActualLoad', '90_ssj_ops', '90_AvgPower', '90_PerfPowerRatio',
'80_ActualLoad', '80_ssj_ops', '80_AvgPower', '80_PerfPowerRatio',
'70_ActualLoad', '70_ssj_ops', '70_AvgPower', '70_PerfPowerRatio',
'60_ActualLoad', '60_ssj_ops', '60_AvgPower', '60_PerfPowerRatio',
'50_ActualLoad', '50_ssj_ops', '50_AvgPower', '50_PerfPowerRatio',
'40_ActualLoad', '40_ssj_ops', '40_AvgPower', '40_PerfPowerRatio',
'30_ActualLoad', '30_ssj_ops', '30_AvgPower', '30_PerfPowerRatio',
'20_ActualLoad', '20_ssj_ops', '20_AvgPower', '20_PerfPowerRatio',
'10_ActualLoad', '10_ssj_ops', '10_AvgPower', '10_PerfPowerRatio', 'ActiveIdle',

'HW_Vendor', 'HW_Model', 'HW_FormFactor', 'HW_CPUName',
'HW_CPUChars', 'HW_CPUFreq', 'HW_CPUsEnabled','HW_HardwareThreads', 
'HW_CPUsOrderable', 'HW_PrimaryCache', 'HW_SecondaryCache','HW_TertiaryCache',
'HW_OtherCache', 'HW_MemAmountGB','HW_DIMMNumAndSize','HW_MemDetails', 
'HW_PSUQuantAndRating', 'HW_PSUDetails','HW_DiskDrive','HW_DiskController',
'HW_NICSNumAndType', 'HW_NICSFirm/OS/Conn','HW_NetSpeedMbit','HW_Keyboard','HW_Mouse',
'HW_Monitor', 'HW_OpticalDrive', 'HW_Other',

'SW_PowerManagement', 'SW_OS', 'SW_OSVersion',
'SW_Filesystem', 'SW_JVMVendor', 'SW_JVMVersion', 'SW_JVMCLIOpts', 
'SW_JVMAffinity', 'SW_JVMInstances', 'SW_JVMInitialHeapMB', 'SW_JVMMaxHeapMB', 
'SW_JVMAddressBits', 'SW_BootFirmwareVersion', 'SW_MgmtFirmwareVersion', 
'SW_WorkloadVersion', 'SW_DirectorLocation', 'SW_Others', 

'SUT_BIOS', 'SUT_Firmware', 'SUT_Notes',
]

# Fixes for broken values in the SPEC results. See the README
with open('../data-updates/spec_data_patches.csv', 'r', encoding='UTF8', newline='') as f:
    patches = list(csv.DictReader(f))

rows = []
rowcount=-1
applied_patches = 0
cut_off_results = 0

# Sorted, because os.scandir returns the files in arbitrary order and the row order should be reproducible
for f in sorted(os.scandir('../spec-power-raw/html/'), key=lambda entry: entry.name):
    if f.is_file():
        rowcount+=1
        result_id = f.name.removesuffix('.html')
        rows.append([result_id])
        o = open(f,'r', encoding='UTF8')
        text = o.read()
        o.close()

        ## Get Test info
        m = re.search(
            r'Test Sponsor:</a></td>$\s*.*>(.*)</td>$'                      # 1
            r'\s*.*SPEC License #:</a></td>$\s*.*>(.*)</td>$'               # 2
            r'\s*.*Test Method:</a></td>$\s*.*>(.*)</td>$\s*</tr>$\s*<tr>$' # 3
            r'\s*.*Tested By:</a></td>$\s*.*>(.*)</td>$'                    # 4
            r'\s*.*Test Location:</a></td>$\s*.*>(.*)</td>$'                # 5
            r'\s*.*Test Date:</a></td>$\s*.*>(.*)</td>$\s*</tr>$\s*<tr>$'   # 6
            r'\s*.*Hardware Availability:</a></td>$\s*.*>(.*)</td>$'        # 7
            r'\s*.*Software Availability:</a></td>$\s*.*>(.*)</td>$'        # 8
            r'\s*.*Publication:</a></td>$\s*.*>(.*)</td>$\s*</tr>$\s*<tr>$' # 9
            r'\s*.*System Source:</a></td>$\s*.*>(.*)</td>$'                # 10
            r'\s*.*System Designation:</a></td>$\s*.*>(.*)</td>$'           # 11
            r'\s*.*Power Provisioning:</a></td>$\s*.*>(.*)</td>$'           # 12
            ,text , re.M)

        if m:
            for x in range(1,13):
                rows[rowcount].append(m.group(x))


        ## Get Power Chart
        for x in range(100, 0, -10):
            m = re.search(f'<td>{x}%</td>$'
                r'\s*<td>(.*)%</td>$'
                r'\s*<td>(.*)</td>$'
                r'\s*<td>(.*)</td>$'
                r'\s*<td>(.*)</td>$'
                , text, re.M)
            if m:
                ssj_ops_cln = re.sub(',', "", m.group(2))
                avg_pwr_cln = re.sub(',', "", m.group(3))
                perf_pwr_ratio_cln = re.sub(',', "", m.group(4))
                rows[rowcount].extend([m.group(1), ssj_ops_cln, avg_pwr_cln
                    , perf_pwr_ratio_cln])
                #print(f"Actual Load: {m.group(1)} --- ssj_ops: {m.group(2)} --- avg.power: {m.group(3)} --- perf.power.ratio: {m.group(4)}\n")
        
        ## Get Idle Power
        m = re.search('Active Idle.*$'
            r'\s*<td>.*</td>$'
            r'\s*<td>(.*)</td>$'
            , text, re.M)
        if m: rows[rowcount].append(re.sub(',', "", m.group(1)))

        ## Get Hardware Info
        m = re.search(r'Hardware Vendor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 1 
            r'\s*.*Model:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                  # 2   
            r'\s*.*Form Factor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 3
            r'\s*.*CPU Name:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'               # 4
            r'\s*.*CPU Characteristics:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'    # 5
            r'\s*.*CPU Frequency \(MHz\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 6
            r'\s*.*CPU\(s\) Enabled:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 7
            r'\s*.*Hardware Threads:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 8
            r'\s*.*CPU\(s\) Orderable:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'     # 9
            r'\s*.*Primary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'          # 10
            r'\s*.*Secondary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'        # 11
            r'\s*.*Tertiary Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 12
            r'\s*.*Other Cache:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 13
            r'\s*.*Memory Amount \(GB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 14 
            r'\s*.*# and size of DIMM:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'     # 15
            r'\s*.*Memory Details:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 16
            r'\s*.*Power Supply Quantity and Rating \(W\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' #17
            r'\s*.*Power Supply Details:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'   # 18
            r'\s*.*Disk Drive:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 19
            r'\s*.*Disk Controller:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'        # 20
            r'\s*.*# and type of Network Interface Cards \(NICs\) Installed:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 21
            r'\s*.*NICs Enabled in Firmware / OS / Connected:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 22
            r'\s*.*Network Speed \(Mbit\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 23
            r'\s*.*Keyboard:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'               # 24
            r'\s*.*Mouse:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                  # 25
            r'\s*.*Monitor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'                # 26
            r'\s*.*Optical Drives:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'         # 27
            r'\s*.*Other Hardware:</a></td>$\s*.*>(.*)</td>'                          # 28
            ,text , re.M)

        if m: #print(m.group(28))
            for x in range(1,29):
                rows[rowcount].append(m.group(x))

        ## Get Software Info
        m = re.search(r'Power Management:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 1
            r'\s*.*Operating System \(OS\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 2   
            r'\s*.*OS Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 3   
            r'\s*.*Filesystem:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 4   
            r'\s*.*JVM Vendor:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'             # 5   
            r'\s*.*JVM Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'            # 6   
            r'\s*.*JVM Command-line Options:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 7   
            r'\s*.*JVM Affinity:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'           # 8
            r'\s*.*JVM Instances:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'          # 9
            r'\s*.*JVM Initial Heap \(MB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 10
            r'\s*.*JVM Maximum Heap \(MB\):</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 11
            r'\s*.*JVM Address Bits:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 12
            r'\s*.*Boot Firmware Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'  # 13
            r'\s*.*Management Firmware Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$' # 14
            r'\s*.*Workload Version:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'       # 15
            r'\s*.*Director Location:</a></td>$\s*.*>(.*)</td>\s*</tr>$\s*<tr>$'      # 16
            r'\s*.*Other Software:</a></td>$\s*.*>(.*)</td>'                          # 17
            ,text , re.M)

        if m: #print(m.group(17))
            for x in range(1, 18):
                rows[rowcount].append(m.group(x))

        ## Get SUT Notes and BIOS / Firmware
        m = re.search(
            r'Boot Firmware Settings</a></div>$\s*<div class=\'freeForm\'>\s*([\w\W]*?)\s*</div>$'              # 1
            r'[\w\W]*?Management Firmware Settings</a></div>$\s*<div class=\'freeForm\'>\s*([\w\W]*?)\s*</div>$'# 2
            r'[\w\W]*?System Under Test Notes</a></div>$\s*<div class=\'freeForm\'>\s*([\w\W]*?)\s*</div>$'     # 3
            ,text , re.M)

        if m:
            for x in range(1,4):
                ### Elements are lists inside. We remove HTML tags and separate by ;;;
                group = re.sub('<li>', ';;;', m.group(x), flags=re.I)
                group = re.sub('</li>|<ul>|</ul>', '', group, flags=re.I).strip()
                rows[rowcount].append(group)

        # The regexes above silently skip a whole group of columns if they do not match
        assert len(rows[rowcount]) == len(header), f"{f.name} has {len(rows[rowcount])} instead of {len(header)} columns"

        for patch in patches:
            if patch['Result_ID'] == result_id:
                column = header.index(patch['Column'])
                # If this fails SPEC has changed the result or the patch is wrong. The patch must then be checked again.
                assert rows[rowcount][column] == patch['Old_Value'], f"Patch for {result_id} expects {patch['Column']} to be '{patch['Old_Value']}', but it is '{rows[rowcount][column]}'"
                rows[rowcount][column] = patch['New_Value']
                applied_patches += 1

        hardware_availability_year = int(rows[rowcount][header.index('Hardware_Availability')].split('-')[1])
        if hardware_availability_year < MIN_HARDWARE_AVAILABILITY_YEAR:
            rows.pop()
            rowcount -= 1
            cut_off_results += 1


assert applied_patches == len(patches), f"Only {applied_patches} of {len(patches)} patches were applied. Please check the Result_IDs."
print(f"Kept {len(rows)} results. Cut off {cut_off_results} results with hardware older than {MIN_HARDWARE_AVAILABILITY_YEAR}. Applied {applied_patches} patches.")

#print(rows)
with open('../data/spec_data.csv', 'w', encoding='UTF8', newline='\n') as f:
    writer = csv.writer(f, delimiter='|')
    writer.writerow(header)
    writer.writerows(rows)
