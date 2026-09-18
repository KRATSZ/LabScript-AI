import { apiService } from '../services/api';

export class ApiTester {
  static async testConnection(): Promise<boolean> {
    try {
      await apiService.healthCheck();
      return true;
    } catch (error) {
      console.error('API connection test failed:', error);
      return false;
    }
  }

  static async testAllEndpoints(): Promise<{
    health: boolean;
    sopGeneration: boolean;
    simulation: boolean;
    tools: boolean;
  }> {
    const results = {
      health: false,
      sopGeneration: false,
      simulation: false,
      tools: false
    };

    // Test health check
    try {
      await apiService.healthCheck();
      results.health = true;
      console.log('✅ Health check passed');
    } catch (error) {
      console.error('❌ Health check failed:', error);
    }

    // Test tools endpoint
    try {
      await apiService.getTools();
      results.tools = true;
      console.log('✅ Tools endpoint passed');
    } catch (error) {
      console.error('❌ Tools endpoint failed:', error);
    }

    // Test SOP generation
    try {
      await apiService.generateSOP({
        hardware_config: 'Robot Model: Opentrons Flex\nAPI Version: 2.20\nLeft Pipette: flex_1channel_1000',
        user_goal: 'Test protocol for API validation'
      });
      results.sopGeneration = true;
      console.log('✅ SOP generation passed');
    } catch (error) {
      console.error('❌ SOP generation test failed:', error);
    }

    // Test simulation
    try {
      const testCode = `from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.20"}

def run(protocol: protocol_api.ProtocolContext):
    # Simple test protocol
    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 'C1')
    pipette = protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])
    trash = protocol.load_trash_bin('A3')
    
    pipette.pick_up_tip()
    pipette.aspirate(100, plate.wells()[0])
    pipette.dispense(100, plate.wells()[1])
    pipette.drop_tip()
`;
      
      await apiService.simulateProtocol({
        protocol_code: testCode
      });
      results.simulation = true;
      console.log('✅ Simulation test passed');
    } catch (error) {
      console.error('❌ Simulation test failed:', error);
    }

    return results;
  }

  static async testCodeGeneration(): Promise<boolean> {
    try {
      console.log('🧪 Testing code generation...');
      
      const result = await apiService.generateProtocolCode(
        {
          sop_markdown: `# Test Protocol

## Materials
- Opentrons Flex robot
- flex_1channel_1000 pipette
- 96-well plate

## Steps
1. Pick up tip
2. Aspirate 100µL from well A1
3. Dispense into well B1
4. Drop tip`,
          hardware_config: 'Robot Model: Opentrons Flex\nAPI Version: 2.20\nLeft Pipette: flex_1channel_1000'
        },
        (progress) => {
          console.log(`📋 Code generation progress: ${progress}`);
        }
      );

      if (result.success && result.generated_code) {
        console.log(`✅ Code generation test passed (${result.attempts} attempts, ${result.generated_code.length} chars)`);
        if (result.warnings.length > 0) {
          console.log(`⚠️ Code generation completed with ${result.warnings.length} warnings`);
        }
        return true;
      } else {
        console.error('❌ Code generation test failed: No code generated');
        return false;
      }
    } catch (error) {
      console.error('❌ Code generation test failed:', error);
      return false;
    }
  }

  static async runFullTest(): Promise<{
    connection: boolean;
    endpoints: {
      health: boolean;
      sopGeneration: boolean;
      simulation: boolean;
      tools: boolean;
    };
    codeGeneration: boolean;
    overall: boolean;
  }> {
    console.log('🚀 Starting full API test suite...');
    
    const connection = await this.testConnection();
    const endpoints = await this.testAllEndpoints();
    const codeGeneration = await this.testCodeGeneration();
    
    const overall = connection && 
                   endpoints.health && 
                   endpoints.sopGeneration && 
                   endpoints.simulation && 
                   endpoints.tools && 
                   codeGeneration;

    console.log('📊 Test Results Summary:');
    console.log(`Connection: ${connection ? '✅' : '❌'}`);
    console.log(`Health: ${endpoints.health ? '✅' : '❌'}`);
    console.log(`SOP Generation: ${endpoints.sopGeneration ? '✅' : '❌'}`);
    console.log(`Simulation: ${endpoints.simulation ? '✅' : '❌'}`);
    console.log(`Tools: ${endpoints.tools ? '✅' : '❌'}`);
    console.log(`Code Generation: ${codeGeneration ? '✅' : '❌'}`);
    console.log(`Overall: ${overall ? '✅ PASS' : '❌ FAIL'}`);

    return {
      connection,
      endpoints,
      codeGeneration,
      overall
    };
  }
} 